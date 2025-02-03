from web3 import Web3
from web3.middleware.geth_poa import geth_poa_middleware
from web3.exceptions import TimeExhausted, TransactionNotFound
import time
from typing import Optional, Dict, Any

class BSCTransactionManager:
    def __init__(self, node_url: str = 'https://data-seed-prebsc-1-s1.binance.org:8545'):
        self.w3 = Web3(Web3.HTTPProvider(node_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.contract = None
        self.DEFAULT_WAIT_TIME = 30  
        self.DEFAULT_RETRIES = 3
        
            
        self.DEFAULT_ABI =[{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"spender","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowances","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[],"stateMutability":"payable","type":"function"},{"stateMutability":"payable","type":"receive"}]


    def check_allowance(self, owner_address: str, spender_address: str) -> int:
        """Check the current allowance"""
        return self.contract.functions.allowance(owner_address, spender_address).call()

    def wait_for_transaction_confirmation(self, tx_hash: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Wait for transaction confirmation with retries
        """
        for attempt in range(max_retries):
            try:
                print(f"Waiting for transaction {tx_hash} confirmation (attempt {attempt + 1}/{max_retries})")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=self.DEFAULT_WAIT_TIME)
                if receipt['status'] == 1:
                    return receipt
                time.sleep(5)  # Wait between retries
            except (TimeExhausted, TransactionNotFound) as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Transaction not confirmed yet, retrying... ({str(e)})")
                time.sleep(10)  # Longer wait between retries
        raise TimeExhausted(f"Transaction {tx_hash} was not confirmed after {max_retries} attempts")

    def build_transaction_params(self, sender_address: str, value: int = 0) -> Dict[str, Any]:
        """Build common transaction parameters"""
        return {
            'from': sender_address,
            'value': value,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': 97,
            'nonce': self.w3.eth.get_transaction_count(sender_address)
        }

    def _send_transaction(self, transaction: Dict[str, Any], private_key: str) -> Dict[str, Any]:
        """Sign and send a transaction with improved error handling"""
        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent: {tx_hash.hex()}")
        
        receipt = self.wait_for_transaction_confirmation(tx_hash.hex())
        return {
            'hash': tx_hash.hex(),
            'status': receipt['status']
        }

    def approve_and_transfer(self, 
                           sender_address: str,
                           recipient_address: str,
                           spender_address: str,
                           amount_in_ether: float,
                           private_key: str,
                           wait_time: int = 15) -> Dict[str, Any]:
        """Approve and transfer tokens with improved handling"""
        if not self.contract:
            raise ValueError("Contract not initialized. Call initialize_contract first.")

        amount = self.w3.to_wei(amount_in_ether, 'ether')
        current_allowance = self.check_allowance(sender_address, spender_address)
        print(f"Current allowance: {self.w3.from_wei(current_allowance, 'ether')} BNB")

        if current_allowance < amount:
            print("Sending approval transaction...")
            tx_params = self.build_transaction_params(sender_address)
            approve_tx = self.contract.functions.approve(
                spender_address,
                amount
            ).build_transaction(tx_params)
            
            approve_result = self._send_transaction(approve_tx, private_key)
            print(f"Approval status: {approve_result['status']}")
            
            print(f"Waiting {wait_time} seconds for approval confirmation...")
            time.sleep(wait_time)
        else:
            print("Sufficient allowance already exists")
            approve_result = {"status": "skipped", "hash": "N/A"}

        new_allowance = self.check_allowance(sender_address, spender_address)
        print(f"New allowance: {self.w3.from_wei(new_allowance, 'ether')} BNB")

        if new_allowance < amount:
            raise ValueError("Insufficient allowance after approval")

        print("Sending transfer transaction...")
        tx_params = self.build_transaction_params(sender_address, amount)
        tx_params['nonce'] = self.w3.eth.get_transaction_count(sender_address)  # Get fresh nonce
        
        transfer_tx = self.contract.functions.transferFrom(
            sender_address,
            recipient_address,
            amount
        ).build_transaction(tx_params)
        
        transfer_result = self._send_transaction(transfer_tx, private_key)
        
        return {
            'approve_transaction': approve_result,
            'transfer_transaction': transfer_result
        }

    def initialize_contract(self, contract_address: str, abi: Optional[list] = None) -> None:
        """Initialize the smart contract"""
        abi = abi or self.DEFAULT_ABI
        self.contract = self.w3.eth.contract(address=contract_address, abi=abi)

    def is_connected(self) -> bool:
        """Check if connected to the BSC network"""
        return self.w3.is_connected()
    
    def check_balance(self, address: str) -> any :
        my_address = self.w3.to_checksum_address(address)
        balance_wei = self.w3.eth.get_balance(my_address)
        balance_tbnb = self.w3.from_wei(balance_wei, 'ether')
        print(f'The balance of tBNB in address {address} is: {balance_tbnb:.5f} tBNB')
        return balance_tbnb

    

def main():
    # Example usage
    manager = BSCTransactionManager()
    print(f"Connected: {manager.is_connected()}")
    
    # Initialize contract
    contract_address = "0xEd25d434a8bc42c1c213fA1a74b96f57c9eE6697"
    manager.initialize_contract(contract_address)
    
    # Transaction parameters
    sender_address = '0x2d0B62bC90a795185ef3048ad9f6DB4eA2cA2ECd'
    recipient_address = '0xe4cE498F8523a32C4093c065113c6960bFe2Ba95'
    spender_address = '0x2d0B62bC90a795185ef3048ad9f6DB4eA2cA2ECd'
    private_key = 'c2af55667e62b5d64c60637b3c2afa00856e0dafae1fbac0e078e2ca47e55978'
    amount_in_ether = 0.05
    
    try:
        result = manager.approve_and_transfer(
            sender_address,
            recipient_address,
            spender_address,
            amount_in_ether,
            private_key,
            wait_time=20  # Increased wait time between approval and transfer
        )
        
        print("\nTransaction Results:")
        print("Approve transaction hash:", result['approve_transaction']['hash'])
        print("Approve transaction status:", result['approve_transaction']['status'])
        print("Transfer transaction hash:", result['transfer_transaction']['hash'])
        print("Transfer transaction status:", result['transfer_transaction']['status'])
    
    except Exception as e:
        print(f"Error executing transactions: {str(e)}")

if __name__ == "__main__":
    main()
