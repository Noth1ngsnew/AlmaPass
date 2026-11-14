// Компилирует AlmaPassNFT.sol и кладёт ABI и байткод в backend/rewards/contract/AlmaPassNFT.json
// Запуск: npm install && npm run compile
const fs = require('fs');
const path = require('path');
const solc = require('solc');

const source = fs.readFileSync(path.join(__dirname, 'AlmaPassNFT.sol'), 'utf8');
const input = {
  language: 'Solidity',
  sources: { 'AlmaPassNFT.sol': { content: source } },
  settings: {
    optimizer: { enabled: true, runs: 200 },
    evmVersion: 'cancun',
    outputSelection: { '*': { '*': ['abi', 'evm.bytecode.object'] } },
  },
};

function findImports(importPath) {
  try {
    return { contents: fs.readFileSync(path.join(__dirname, 'node_modules', importPath), 'utf8') };
  } catch {
    return { error: `File not found: ${importPath}` };
  }
}

const output = JSON.parse(solc.compile(JSON.stringify(input), { import: findImports }));
const errors = (output.errors || []).filter((item) => item.severity === 'error');
if (errors.length) {
  errors.forEach((item) => console.error(item.formattedMessage));
  process.exit(1);
}

const contract = output.contracts['AlmaPassNFT.sol'].AlmaPassNFT;
const target = path.join(__dirname, '..', 'backend', 'rewards', 'contract', 'AlmaPassNFT.json');
fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(
  target,
  JSON.stringify({ contractName: 'AlmaPassNFT', compiler: solc.version(), abi: contract.abi, bytecode: '0x' + contract.evm.bytecode.object }, null, 2) + '\n',
);
console.log(`Compiled with solc ${solc.version()} -> ${path.relative(process.cwd(), target)}`);
