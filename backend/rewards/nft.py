"""Выдача NFT за посещение: подпись и отправка транзакции в сеть от имени серверного кошелька."""

import json
import threading
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone
from web3 import Web3
from web3.logs import DISCARD
from web3.middleware import ExtraDataToPOAMiddleware

from .models import NFTReward

ARTIFACT_PATH = Path(__file__).parent / 'contract' / 'AlmaPassNFT.json'
RECEIPT_TIMEOUT = 180  # секунд ждём подтверждения транзакции

# Транзакции одного кошелька должны идти по очереди, иначе совпадут номера (nonce)
_mint_lock = threading.Lock()


class NFTError(Exception):
    """Ошибка с кодом, который понимает фронтенд."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@lru_cache(maxsize=1)
def load_artifact():
    return json.loads(ARTIFACT_PATH.read_text())


def is_configured():
    return bool(settings.NFT_PRIVATE_KEY and settings.NFT_CONTRACT_ADDRESS)


def is_valid_wallet(address):
    return bool(address) and Web3.is_address(address)


@lru_cache(maxsize=1)
def get_web3():
    w3 = Web3(Web3.HTTPProvider(settings.NFT_RPC_URL, request_kwargs={'timeout': 30}))
    # Polygon — сеть типа Proof-of-Authority: её блоки содержат удлинённое поле extraData,
    # и без этой настройки web3 отказывается их читать
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_account(w3):
    if not settings.NFT_PRIVATE_KEY:
        raise NFTError('not_configured', 'NFT_PRIVATE_KEY is not set. Run: python manage.py create_nft_wallet')
    return w3.eth.account.from_key(settings.NFT_PRIVATE_KEY)


def get_contract(w3):
    if not settings.NFT_CONTRACT_ADDRESS:
        raise NFTError('not_configured', 'NFT_CONTRACT_ADDRESS is not set. Run: python manage.py deploy_nft_contract')
    return w3.eth.contract(address=Web3.to_checksum_address(settings.NFT_CONTRACT_ADDRESS),
                           abi=load_artifact()['abi'])


def send_transaction(w3, account, call):
    """Собирает, подписывает и отправляет транзакцию; возвращает квитанцию."""
    tx = call.build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address, 'pending'),
        'chainId': w3.eth.chain_id,
    })
    tx['gas'] = int(tx['gas'] * 1.2)  # запас на случай колебаний
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=RECEIPT_TIMEOUT)


def deploy_contract():
    """Публикует контракт AlmaPassNFT и возвращает его адрес."""
    w3 = get_web3()
    account = get_account(w3)
    artifact = load_artifact()
    factory = w3.eth.contract(abi=artifact['abi'], bytecode=artifact['bytecode'])
    receipt = send_transaction(w3, account, factory.constructor())
    if receipt.status != 1:
        raise NFTError('deploy_failed', f'Deployment transaction failed: {receipt.transactionHash.to_0x_hex()}')
    return receipt.contractAddress


def metadata_uri(reward):
    return f'{settings.PUBLIC_API_URL}/api/nft/metadata/{reward.id}/'


def mint_reward(reward_id):
    """Выдаёт NFT по записи NFTReward. Результат (успех или ошибка) сохраняется в саму запись."""
    with _mint_lock:
        reward = NFTReward.objects.select_related('visit__event', 'visit__user').get(pk=reward_id)
        if reward.status == NFTReward.Status.MINTED:
            return reward
        try:
            if not is_valid_wallet(reward.wallet_address):
                raise NFTError('no_wallet', 'Wallet address is missing or invalid.')
            w3 = get_web3()
            account = get_account(w3)
            contract = get_contract(w3)
            wallet = Web3.to_checksum_address(reward.wallet_address)
            uri = metadata_uri(reward)

            reward.status = NFTReward.Status.MINTING
            reward.error = ''
            reward.save(update_fields=['status', 'error'])

            receipt = send_transaction(w3, account, contract.functions.mint(wallet, reward.visit.event_id, uri))
            reward.tx_hash = receipt.transactionHash.to_0x_hex()
            if receipt.status != 1:
                raise NFTError('tx_failed', 'Transaction was reverted by the network.')

            logs = contract.events.AttendanceMinted().process_receipt(receipt, errors=DISCARD)
            reward.token_id = logs[0]['args']['tokenId']
            reward.contract_address = contract.address
            reward.metadata_uri = uri
            reward.status = NFTReward.Status.MINTED
            reward.minted_at = timezone.now()
        except Exception as exc:  # noqa: BLE001 — любая ошибка сети должна попасть в запись, а не уронить поток
            reward.status = NFTReward.Status.FAILED
            reward.error = f'{getattr(exc, "code", type(exc).__name__)}: {exc}'[:1000]
        reward.save()
        return reward


def start_mint(reward):
    """Запускает выдачу: в фоне (по умолчанию) или сразу, если NFT_MINT_ASYNC=0."""
    reward.status = NFTReward.Status.MINTING
    reward.error = ''
    reward.save(update_fields=['status', 'error'])

    if not settings.NFT_MINT_ASYNC:
        return mint_reward(reward.id)

    def run():
        try:
            mint_reward(reward.id)
        finally:
            connection.close()

    threading.Thread(target=run, daemon=True, name=f'mint-{reward.id}').start()
    return reward
