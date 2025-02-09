from datetime import datetime
from eth_account import Account
import telebot
from web3 import Web3
from transaction_manager import BSCTransactionManager
from wallet_manager import WalletManager
# si j'ai plusieurs instances ithetelfara ?
# ajouter un pending sur l'envoi 
# Create a class to store global variables
class UserData:
    def __init__(self):
        self.phone_number = None
        self.last_command = None
        self.pending_private_key = None


user_sessions = {}

def get_user_session(chat_id):
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserData()
    return user_sessions[chat_id]




bot = telebot.TeleBot("7471308316:AAHsoPMASL2YvyZkT1R8z5XFxgUll5b-XTM")
tm = BSCTransactionManager()
contract_address = Web3.to_checksum_address("0xEd25d434a8bc42c1c213fA1a74b96f57c9eE6697")
collaboratif_payment_contract = Web3.to_checksum_address("0x48ace74fdaaf87e32b71ff4fc8ed752389424153")
tm.initialize_contracts(contract_address,collaboratif_payment_contract)
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
        "/deconnect - Deconnectez vous du serveur\n"
        "/address - Récuperez votre adresse\n"
        "/creategroup <montant> <beneficiaire> <description> - Créer un groupe de paiement\n"
        "/contribute <group_id> <montant> - Contribuer à un groupe\n"
        "/groupinfo <group_id> - Voir les infos d'un groupe")


@bot.message_handler(commands=['connection'])
def request_connection(message):
    user_session = get_user_session(message.chat.id)  # Obtenir la session de l'utilisateur
    user_session.last_command = 'connection'
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
    
    user_session = get_user_session(message.chat.id)  # Obtenir la session de l'utilisateur
    user_session.last_command = 'create_wallet'

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
    user_session = get_user_session(message.chat.id)

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
            
            user_session.pending_private_key = private_key
            user_session.last_command = 'register'
            
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
    user_session = get_user_session(message.chat.id)
    phone_number = '+'+ message.contact.phone_number
    
    if user_session.last_command == 'connection':
        print("connection")
        if wm.check_phone_exists(phone_number):
            user_session.phone_number = phone_number  
            bot.reply_to(message, "Connexion réussie ! Tu peux maintenant utiliser le bot.")
        else:
            bot.reply_to(message, "Tu n'as pas encore de wallet associée à ce numéro de telephone ! Si tu veux en créer un utilise /create_wallet")
    
    elif user_session.last_command == 'create_wallet':
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
    user_session = get_user_session(message.chat.id)
    
    
    if not user_session.phone_number:
        bot.reply_to(message, "Tu dois d'abord te connecter avec /connection")
        return        
    balance = tm.check_balance(wm.get_user_address(user_session.phone_number))
    bot.reply_to(message, f"Le solde du compte est de {balance} BNB")



@bot.message_handler(commands=['send'])
def handle_send(message):
    user_session = get_user_session(message.chat.id)

    if not user_session.phone_number:
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
            sender_address = wm.get_user_address(user_session.phone_number)
            result = tm.approve_and_transfer(
                sender_address,                               # sender
                address,                                      # recipient
                sender_address,                               # spender (même que sender)
                amount,
                wm.get_user_private_key(user_session.phone_number),
                wait_time=20
            )
            bot.reply_to(message, f"Transaction envoyée avec succès!\nApprove: {result['approve_transaction']['hash']}\nTransfer: {result['transfer_transaction']['hash']}")
        except Exception as e:
            bot.reply_to(message, f"Erreur lors de la transaction: {str(e)}")
   
    except Exception as e:
        bot.reply_to(message, f"Erreur: {str(e)}")



@bot.message_handler(commands=['creategroup'])
def create_group(message):
    user_session = get_user_session(message.chat.id)

    if not user_session.phone_number:
        bot.reply_to(message, "Tu dois d'abord te connecter avec /connection")
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "Format incorrect. Utilise: /creategroup <montant> <beneficiaire> <description>")
            return
            
        amount = float(parts[1])
        beneficiary = parts[2]
        description = ' '.join(parts[3:])
            
        if not beneficiary.startswith('0x') or len(beneficiary) != 42:
            bot.reply_to(message, "Adresse du bénéficiaire invalide")
            return
            
        creator_address = wm.get_user_address(user_session.phone_number)
        private_key = wm.get_user_private_key(user_session.phone_number)            
        result = tm.create_group_payment(
            creator_address,
            amount,
            beneficiary,
            private_key
        )
        
        group_id = result.get('group_id', result['hash'])
        details = tm.get_group_details(group_id)
        
        bot.reply_to(
            message,
            f"✅ Groupe de paiement créé !\n"
            f"ID du groupe: {group_id}\n"
            f"Montant cible: {amount} BNB\n"
            f"Créateur: {details['owner']}\n"
            f"Bénéficiaire: {details['beneficiary']}\n"
            f"Description: {description}\n\n"
            f"Pour contribuer, utilisez:\n"
            f"/contribute {group_id} <montant>"
        )
            
    except Exception as e:
        bot.reply_to(message, f"❌ Erreur: {str(e)}")




@bot.message_handler(commands=['address'])
def get_address(message):
    user_session = get_user_session(message.chat.id)

    if not user_session.phone_number:
        bot.reply_to(message, "Tu dois d'abord te connecter avec /connection")
        return
    address= wm.get_user_address(user_session.phone_number)
    response = (
            f"✅ Addresse :{address} \n"
        )
        
    bot.reply_to(message, response)

@bot.message_handler(commands=['contribute'])
def contribute_to_group(message):
    user_session = get_user_session(message.chat.id)

    if not user_session.phone_number:
        bot.reply_to(message, "Tu dois d'abord te connecter avec /connection")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Format incorrect. Utilise: /contribute <group_id> <montant>")
            return
        
        group_id = parts[1]
        amount = float(parts[2])
        
        group_details = tm.get_group_details(group_id)
        if group_details['completed']:
            bot.reply_to(message, "Ce groupe de paiement est déjà terminé")
            return
        
        from_address = wm.get_user_address(user_session.phone_number)
        private_key = wm.get_user_private_key(user_session.phone_number)
        
        result = tm.contribute_to_group(
            group_id,
            from_address,
            amount,
            private_key
        )
        
        current_balance = tm.get_group_balance(group_id)
        target_amount = group_details['targetAmount']
        
        response = (
            f"✅ Contribution effectuée !\n"
            f"Montant: {amount} BNB\n"
            f"Transaction: {result['hash']}\n"
            f"Progress: {current_balance}/{target_amount} BNB ({(current_balance/target_amount)*100:.1f}%)"
        )
        
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Erreur: {str(e)}")

@bot.message_handler(commands=['groupinfo'])
def get_group_info(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Format incorrect. Utilise: /groupinfo <group_id>")
            return
        
        group_id = parts[1]
        details = tm.get_group_details(group_id)
        current_balance = tm.get_group_balance(group_id)
        
        # Ajout d'une vérification pour éviter la division par zéro
        if details['targetAmount'] == 0:
            progress = 0
        else:
            progress = (current_balance/details['targetAmount'])*100
            
        response = (
            f"📊 Informations du groupe\n\n"
            f"Créateur: {details['owner']}\n"
            f"Montant cible: {details['targetAmount']} BNB\n"
            f"Montant actuel: {current_balance} BNB\n"
            f"Progress: {progress:.1f}%\n"
            f"Statut: {'✅ Complété' if details['completed'] else '⏳ En cours'}\n"
            f"Bénéficiaire: {details['beneficiary']}\n"
            f"Nombre de contributeurs: {len(details['contributors'])}"
        )
        
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Erreur: {str(e)}")





bot.polling()