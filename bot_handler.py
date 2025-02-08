from eth_account import Account
import telebot
from transaction_manager import BSCTransactionManager
from wallet_manager import WalletManager
# si j'ai plusieurs instances ithetelfara ?
# ajouter un pending sur l'envoi 
# Create a class to store global variables
class UserData:
    def __init__(self):
        self.phone_number = None

# Initialize the global data
user_data = UserData()

bot = telebot.TeleBot("7471308316:AAHsoPMASL2YvyZkT1R8z5XFxgUll5b-XTM")
tm = BSCTransactionManager()
contract_address = "0xEd25d434a8bc42c1c213fA1a74b96f57c9eE6697"
collaboratif_payment_contract="0x4EAcF7b4b0023B336fa91ce7439fF0b5dD3fED4D"
tm.initialize_contract(contract_address)
wm = WalletManager()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bonjour à toi le boss ! Tu vas bien ? \n"
        "Commandes:\n"
        "/connection - Connectez vous à votre wallet\n"
        "/register <private_key> - Register your wallet\n"
        "/create_wallet - Créer votre wallet\n"
        "/balance - Regardez la balance de votre wallet\n"
        "/send <address> <amount> - Envoyez des BNB à une addresse\n"
        "/deconnect - Deconnectez vous du serveur"
        "/address - Récuperez votre adresse")

@bot.message_handler(commands=['connection'])
def request_connection(message):
    user_data.last_command = 'connection'
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    button = telebot.types.KeyboardButton(text="Share Phone Number", request_contact=True)
    markup.add(button)
    
    bot.send_message(
        message.chat.id,
        "Pour te connecter merci de partager ton numéro de téléphone !",
        reply_markup=markup
    )


@bot.message_handler(commands=['create_wallet'])
def request_phone_for_wallet(message):
    user_data.last_command = 'create_wallet'
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    button = telebot.types.KeyboardButton(text="Share Phone Number", request_contact=True)
    markup.add(button)
   
    bot.send_message(
        message.chat.id,
        "Pour créer ton wallet, partage d'abord ton numéro de téléphone !",
        reply_markup=markup
    )

@bot.message_handler(commands=['register'])
def handle_register(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Format incorrect. Utilise: /register <private_key>")
            return
        
        private_key = parts[1]
        
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
            
        try:
            account = Account.from_key(private_key)
            derived_address = account.address
            print(f"Derived address from private key: {derived_address}")
            
            user_data.pending_private_key = private_key
            user_data.last_command = 'register'
            
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
            button = telebot.types.KeyboardButton(text="Share Phone Number", request_contact=True)
            markup.add(button)
            
            bot.send_message(
                message.chat.id,
                "Private key valide ! Pour finaliser l'enregistrement, partage ton numéro de téléphone.",
                reply_markup=markup
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Clé privée invalide: {str(e)}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Erreur: {str(e)}")

@bot.message_handler(content_types=['contact'])
def handle_all_contacts(message):
    phone_number = '+'+ message.contact.phone_number
    
    if user_data.last_command == 'connection':
        print("connection")
        if wm.check_phone_exists(phone_number):
            user_data.phone_number = phone_number  
            bot.reply_to(message, "Connexion réussie ! Tu peux maintenant utiliser le bot.")
        else:
            bot.reply_to(message, "Tu n'as pas encore de wallet associée à ce numéro de telephone ! Si tu veux en créer un utilise /create_wallet")
    
    elif user_data.last_command == 'create_wallet':
        print("creation")
        if not wm.check_phone_exists( phone_number):
            result = wm.process_phone_number(phone_number)
            if result["success"]:
                response_message = (
                    f"✅ {result['message']}\n\n"
                    f"📱 Numéro: {result['data']['phone_number']}\n"
                    f"🔑 Adresse du wallet: {result['data']['wallet_address']}\n\n"
                    f"Tu peux maintenant utiliser les commandes du bot, commence par te connecter !"
                )
                bot.reply_to(message, response_message)
            else:
                bot.reply_to(message, f"❌ {result['message']}") 
        else:   
            bot.reply_to(message, f"❌ Tu as déjà un wallet associé à ce numéro de telephone !\nSi tu veux en associer un nouveau utilise /associate_wallet") 
               



@bot.message_handler(commands=['balance'])
def check_balance(message):
    if not user_data.phone_number:
        bot.reply_to(message, "Tu dois d'abord te connecter avec /connection")
        return        
    balance = tm.check_balance(wm.get_user_address(user_data.phone_number))
    bot.reply_to(message, f"Le solde du compte est de {balance} BNB")



@bot.message_handler(commands=['send'])
def handle_send(message):
    if not user_data.phone_number:
        bot.reply_to(message, "Tu dois d'abord te connecter avec /connection")
        return
       
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Format incorrect. Utilise: /send <address> <amount>")
            return
       
        _, address, amount = parts
        if not address.startswith('0x') or len(address) != 42:
            bot.reply_to(message, "Addresse BNB invalide")
            return
       
        try:
            amount = float(amount)
        except ValueError:
            bot.reply_to(message, "Le montant doit être un nombre")
            return
       
        try:
            sender_address = wm.get_user_address(user_data.phone_number)
            result = tm.approve_and_transfer(
                sender_address,                               # sender
                address,                                      # recipient
                sender_address,                               # spender (même que sender)
                amount,
                wm.get_user_private_key(user_data.phone_number),
                wait_time=20
            )
            bot.reply_to(message, f"Transaction envoyée avec succès!\nApprove: {result['approve_transaction']['hash']}\nTransfer: {result['transfer_transaction']['hash']}")
        except Exception as e:
            bot.reply_to(message, f"Erreur lors de la transaction: {str(e)}")
   
    except Exception as e:
        bot.reply_to(message, f"Erreur: {str(e)}")



bot.polling()