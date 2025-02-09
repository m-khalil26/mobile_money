from web3 import Web3
from web3.middleware.geth_poa import geth_poa_middleware
from web3.exceptions import TimeExhausted, TransactionNotFound
import time
from typing import Optional, Dict, Any

class BSCTransactionManager:
    def __init__(self, node_url: str = 'https://data-seed-prebsc-1-s1.binance.org:8545'):
        self.w3 = Web3(Web3.HTTPProvider(node_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.transfer_contract = None
        self.DEFAULT_WAIT_TIME = 30  
        self.DEFAULT_RETRIES = 3
        
            
        self.TRANSFER_ABI  =[{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"spender","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowances","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[],"stateMutability":"payable","type":"function"},{"stateMutability":"payable","type":"receive"}]
        self.GROUP_PAYMENT_ABI = [{"anonymous":True,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"spender","type":"address"},{"indexed":True,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":True,"inputs":[{"indexed":True,"internalType":"bytes32","name":"groupId","type":"bytes32"},{"indexed":True,"internalType":"address","name":"contributor","type":"address"},{"indexed":True,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Contribution","type":"event"},{"anonymous":True,"inputs":[{"indexed":True,"internalType":"bytes32","name":"groupId","type":"bytes32"},{"indexed":True,"internalType":"uint256","name":"totalAmount","type":"uint256"}],"name":"GroupCompleted","type":"event"},{"anonymous":True,"inputs":[{"indexed":True,"internalType":"bytes32","name":"groupId","type":"bytes32"},{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"uint256","name":"targetAmount","type":"uint256"}],"name":"GroupCreated","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowances","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"groupId","type":"bytes32"},{"internalType":"address","name":"from","type":"address"}],"name":"contribute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_targetAmount","type":"uint256"},{"internalType":"address payable","name":"_beneficiary","type":"address"}],"name":"createPaymentGroup","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"groupId","type":"bytes32"},{"internalType":"address","name":"contributor","type":"address"}],"name":"getContribution","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"groupId","type":"bytes32"}],"name":"getGroupBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"groupId","type":"bytes32"}],"name":"getGroupDetails","outputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"uint256","name":"targetAmount","type":"uint256"},{"internalType":"bool","name":"completed","type":"bool"},{"internalType":"address[]","name":"contributors","type":"address[]"},{"internalType":"address","name":"beneficiary","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"paymentGroups","outputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"uint256","name":"targetAmount","type":"uint256"},{"internalType":"bool","name":"completed","type":"bool"},{"internalType":"address payable","name":"beneficiary","type":"address"}],"stateMutability":"view","type":"function"},{"stateMutability":"payable","type":"receive"}]

    def initialize_contracts(self, transfer_address: str, group_payment_address: str) -> None:
        """Initialize both smart contracts"""
        self.transfer_contract = self.w3.eth.contract(
            address=transfer_address, 
            abi=self.TRANSFER_ABI
        )
        self.group_payment_contract = self.w3.eth.contract(
            address=group_payment_address, 
            abi=self.GROUP_PAYMENT_ABI
        )

    def check_allowance(self, owner_address: str, spender_address: str) -> int:
        return self.transfer_contract.functions.allowance(owner_address, spender_address).call()


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
        if not self.transfer_contract:
            raise ValueError("Transfer contract not initialized")
   

        amount = self.w3.to_wei(amount_in_ether, 'ether')
        current_allowance = self.check_allowance(sender_address, spender_address)
        print(f"Current allowance: {self.w3.from_wei(current_allowance, 'ether')} BNB")

        if current_allowance < amount:
            print("Sending approval transaction...")
            tx_params = self.build_transaction_params(sender_address)
            approve_tx = self.transfer_contract.functions.approve(
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
        
        transfer_tx = self.transfer_contract.functions.transferFrom(
            sender_address,
            recipient_address,
            amount
        ).build_transaction(tx_params)
        
        transfer_result = self._send_transaction(transfer_tx, private_key)
        
        return {
            'approve_transaction': approve_result,
            'transfer_transaction': transfer_result
        }



    def is_connected(self) -> bool:
        """Check if connected to the BSC network"""
        return self.w3.is_connected()
    
    def check_balance(self, address: str) -> any :
        my_address = self.w3.to_checksum_address(address)
        balance_wei = self.w3.eth.get_balance(my_address)
        balance_tbnb = self.w3.from_wei(balance_wei, 'ether')
        print(f'The balance of tBNB in address {address} is: {balance_tbnb:.5f} tBNB')
        return balance_tbnb
    
    def create_group_payment(self, creator_address: str, target_amount: float, 
                        beneficiary: str, private_key: str) -> Dict[str, Any]:
        if not self.group_payment_contract:
            raise ValueError("Group payment contract not initialized")
                
        amount_wei = self.w3.to_wei(target_amount, 'ether')
        tx_params = self.build_transaction_params(creator_address)
        
        create_tx = self.group_payment_contract.functions.createPaymentGroup(
            amount_wei,      
            beneficiary    
        ).build_transaction(tx_params)
        
        result = self._send_transaction(create_tx, private_key)
        
        receipt = self.w3.eth.get_transaction_receipt(result['hash'])
        
        for log in receipt['logs']:
            if len(log['topics']) >= 2:
                result['group_id'] = log['topics'][1].hex()
                break
        
        if 'group_id' not in result:
            raise ValueError("Could not find group ID in transaction logs")
            
        print(f"Group created with ID: {result['group_id']}")
        return result
    
    
    def get_group_details(self, group_id: str) -> Dict[str, Any]:
        """Get details of a group payment"""
        if not self.group_payment_contract:
            raise ValueError("Group payment contract not initialized")
        
        details = self.group_payment_contract.functions.getGroupDetails(group_id).call()
        return {
            'owner': details[0],
            'targetAmount': self.w3.from_wei(details[1], 'ether'),
            'completed': details[2],
            'contributors': details[3],
            'beneficiary': details[4]
        }
    def contribute_to_group(self, group_id: str, from_address: str, 
                          amount: float, private_key: str) -> Dict[str, Any]:
        if not self.group_payment_contract:
            raise ValueError("Group payment contract not initialized")
            
        amount_wei = self.w3.to_wei(amount, 'ether')
        tx_params = self.build_transaction_params(from_address, amount_wei)
        
        contribute_tx = self.group_payment_contract.functions.contribute(
            group_id,
            from_address
        ).build_transaction(tx_params)
        
        return self._send_transaction(contribute_tx, private_key)
    

    def get_group_balance(self, group_id: str) -> float:
        """Get total balance of a group"""
        if not self.group_payment_contract:
            raise ValueError("Group payment contract not initialized")
        
        balance_wei = self.group_payment_contract.functions.getGroupBalance(group_id).call()
        return self.w3.from_wei(balance_wei, 'ether')

    

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