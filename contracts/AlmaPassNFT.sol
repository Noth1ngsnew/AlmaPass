// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ERC721URIStorage} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title AlmaPass — NFT за посещение городских событий Алматы
/// @notice Токен выдаёт только владелец контракта (сервер AlmaPass) после подтверждённого check-in.
contract AlmaPassNFT is ERC721URIStorage, Ownable {
    uint256 private _nextTokenId = 1;

    /// @notice Событие платформы, за которое выдан токен
    mapping(uint256 tokenId => uint256 eventId) public eventOf;

    /// @dev Защита от повторной выдачи: один токен на пару «кошелёк — событие»
    mapping(address visitor => mapping(uint256 eventId => bool)) public hasAttended;

    event AttendanceMinted(address indexed visitor, uint256 indexed eventId, uint256 tokenId);

    error AlreadyMinted(address visitor, uint256 eventId);

    constructor() ERC721("AlmaPass", "ALMA") Ownable(msg.sender) {}

    /// @notice Выдать NFT посетителю события
    /// @param to кошелёк посетителя
    /// @param eventId идентификатор события на платформе
    /// @param uri ссылка на метаданные токена (JSON)
    function mint(address to, uint256 eventId, string calldata uri) external onlyOwner returns (uint256 tokenId) {
        if (hasAttended[to][eventId]) revert AlreadyMinted(to, eventId);
        hasAttended[to][eventId] = true;

        tokenId = _nextTokenId++;
        eventOf[tokenId] = eventId;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);

        emit AttendanceMinted(to, eventId, tokenId);
    }

    /// @notice Сколько токенов выдано всего
    function totalMinted() external view returns (uint256) {
        return _nextTokenId - 1;
    }
}
