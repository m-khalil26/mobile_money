import psycopg2
from eth_account import Account
import secrets
import phonenumbers

class WalletManager:
    def __init__(self, db_host="localhost", db_name="wallet_db", db_user="admin", db_password="change_this_password"):
        """Initialize database connection parameters"""
        self.db_params = {
            "host": db_host,
            "database": db_name,
            "user": db_user,
            "password": db_password
        }

    def validate_phone_number(self, phone_number):
        """Validate phone number format"""
        try:
            parsed_number = phonenumbers.parse(phone_number)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number format")
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except Exception as e:
            raise ValueError(f"Phone number validation error: {str(e)}")

    def check_phone_exists(self, phone_number):
        """Check if phone number exists in database"""
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT phone_number FROM wallet_info WHERE phone_number = %s", (phone_number,))
                return cur.fetchone() is not None

    def create_wallet(self):
        """Create a new Ethereum wallet"""
        Account.enable_unaudited_hdwallet_features()
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        
        return {
            "address": account.address,
            "private_key": private_key
        }

    def store_wallet(self, phone_number, wallet_address, private_key):
        """Store wallet information in database"""
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO wallet_info (phone_number, wallet_address, private_key)
                    VALUES (%s, %s, %s)
                    """,
                    (phone_number, wallet_address, private_key)
                )
            conn.commit()

    def get_user_address(self, phone_number):
        """Retrieve wallet address from database based on phone number"""
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT wallet_address 
                    FROM wallet_info 
                    WHERE phone_number = %s
                    """,
                    (phone_number,)
                )
                result = cur.fetchone()
                
                if result:
                    return result[0]  
                return None  
            

    def get_user_private_key(self, phone_number):
        """Retrieve private key from database based on phone number"""
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT private_key 
                    FROM wallet_info 
                    WHERE phone_number = %s
                    """,
                    (phone_number,)
                )
                result = cur.fetchone()
                
                if result:
                    return result[0]  
                return None  

    def process_phone_number(self, phone_number):
        """Main function to process phone number and create wallet"""
        try:
            validated_number = self.validate_phone_number(phone_number)
            
            if self.check_phone_exists(validated_number):
                return {
                    "success": False,
                    "message": "Phone number already has a wallet associated"
                }
            
            wallet = self.create_wallet()
            
            self.store_wallet(validated_number, wallet["address"], wallet["private_key"])
            
            return {
                "success": True,
                "message": "Wallet created successfully",
                "data": {
                    "phone_number": validated_number,
                    "wallet_address": wallet["address"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}"
            }


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python script.py <phone_number>")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    wallet_manager = WalletManager()
    result = wallet_manager.process_phone_number(phone_number)
    print(result)

if __name__ == "__main__":
    main()