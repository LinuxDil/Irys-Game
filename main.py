from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, random, secrets, string, time, json, re, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class Irys:
    def __init__(self) -> None:
        self.BASE_API = "https://play.irys.xyz/api"
        self.RPC_URL = "https://testnet-rpc.irys.xyz/v1/execution-rpc"
        self.EXPLORER = "https://testnet-explorer.irys.xyz/tx/"
        self.NATIVE_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000000"
        self.ARCADE_BANK_ADDRESS = "0xBC41F2B6BdFCB3D87c3d5E8b37fD02C56B69ccaC"
        self.CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"getUserBalance","stateMutability":"view","inputs":[{"name":"user","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"deposit","stateMutability":"payable","inputs":[],"outputs":[]},
            {"type":"function","name":"withdraw","stateMutability":"nonpayable","inputs":[{"name":"amount","type":"uint256"}],"outputs":[]}
        ]''')
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.used_nonce = {}
        self.bank_option = 0
        self.deposit_amount = 0
        self.withdraw_amount = 0
        self.snake_game_count = 0
        self.asteroids_game_count = 0
        self.hexshot_game_count = 0
        self.missile_game_count = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Irys Game{Fore.BLUE + Style.BRIGHT} Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate Address Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}                  "
            )
            return None
        
    def generate_random_string(self, length=9):
        characters = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
        
    def generate_game_payload(self, account: str, address: str, game_id: str, score: int, start_timestamp: int, game_type: str, payload_type: str):
        try:
            if payload_type == "Start":
                message = f"I authorize payment of 0.001 IRYS to play a game on Irys Arcade.\n    \nPlayer: {address}\nAmount: 0.001 IRYS\nTimestamp: {start_timestamp}\n\nThis signature confirms I own this wallet and authorize the payment."

            elif payload_type == "Complete":
                complete_timestamp = int(time.time()) * 1000
                message = f"I completed a {game_type} game on Irys Arcade.\n    \nPlayer: {address}\nGame: {game_type}\nScore: {score}\nSession: game_{start_timestamp}_{game_id}\nTimestamp: {complete_timestamp}\n\nThis signature confirms I own this wallet and completed this game."

            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            if payload_type == "Start":
                payload = {
                    "playerAddress": address,
                    "gameCost": 0.001,
                    "signature": signature,
                    "message": message,
                    "timestamp": start_timestamp,
                    "sessionId": f"game_{start_timestamp}_{game_id}",
                    "gameType": game_type
                }

            elif payload_type == "Complete":
                payload = {
                    "playerAddress": address,
                    "gameType": game_type,
                    "score": score,
                    "signature": signature,
                    "message": message,
                    "timestamp": complete_timestamp,
                    "sessionId": f"game_{start_timestamp}_{game_id}"
                }

            return payload
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")
    
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
            
    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Send TX Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Wait for Receipt Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")
        
    async def get_token_balance(self, address: str, contract_address: str, use_proxy: bool, retries=5):
        for attempt in range(retries):
            try:
                web3 = await self.get_web3_with_check(address, use_proxy)

                if contract_address == self.NATIVE_TOKEN_ADDRESS:
                    balance = web3.eth.get_balance(address)
                else:
                    token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.CONTRACT_ABI)
                    balance = token_contract.functions.getUserBalance(address).call()

                token_balance = balance / (10**18)

                return token_balance
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                return None
            
    async def perform_deposit(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            asset_address = web3.to_checksum_address(self.ARCADE_BANK_ADDRESS)
            amount_to_wei = web3.to_wei(self.deposit_amount, "ether")

            token_contract = web3.eth.contract(address=asset_address, abi=self.CONTRACT_ABI)
            deposit_data = token_contract.functions.deposit()

            estimated_gas = deposit_data.estimate_gas({"from":address, "value":amount_to_wei})
            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = max_priority_fee

            deposit_tx = deposit_data.build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, deposit_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def perform_withdraw(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            asset_address = web3.to_checksum_address(self.ARCADE_BANK_ADDRESS)
            amount_to_wei = web3.to_wei(self.withdraw_amount, "ether")

            token_contract = web3.eth.contract(address=asset_address, abi=self.CONTRACT_ABI)
            withdraw_data = token_contract.functions.withdraw(amount_to_wei)

            estimated_gas = withdraw_data.estimate_gas({"from":address})
            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = max_priority_fee

            withdraw_tx = withdraw_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, withdraw_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    def print_deposit_question(self):
        while True:
            try:
                deposit_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Deposit Amount -> {Style.RESET_ALL}").strip())
                if deposit_amount > 0:
                    self.deposit_amount = deposit_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")
    
    def print_withdraw_question(self):
        while True:
            try:
                withdraw_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Withdraw Amount -> {Style.RESET_ALL}").strip())
                if withdraw_amount > 0:
                    self.withdraw_amount = withdraw_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

    def print_bank_question(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Deposit IRYS{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Withdraw IRYS{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Skipped{Style.RESET_ALL}")
                bank_option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if bank_option in [1, 2, 3]:
                    wrap_type = (
                        "Deposit IRYS" if bank_option == 1 else 
                        "Withdraw IRYS" if bank_option == 2 else 
                        "Skipped"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{wrap_type} Selected.{Style.RESET_ALL}")
                    self.bank_option = bank_option

                    if self.bank_option == 1:
                        self.print_deposit_question()
                    elif self.bank_option == 2:
                        self.print_withdraw_question()

                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

    def print_game_count_question(self, game_type: str):
        while True:
            try:
                game_count = int(input(f"{Fore.BLUE + Style.BRIGHT}Enter Game Count [{game_type}] -> {Style.RESET_ALL}").strip())
                if game_count >= 0:
                    if game_type == "Snake":
                        self.snake_game_count = game_count
                    elif game_type == "Asteroids":
                        self.asteroids_game_count = game_count
                    elif game_type == "Hexshot":
                        self.hexshot_game_count = game_count
                    elif game_type == "Missile":
                        self.missile_game_count = game_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}{game_type} Count must be >= 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Fore.MAGENTA + Style.BRIGHT}Min Delay For Each Game -> {Style.RESET_ALL}").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                max_delay = int(input(f"{Fore.MAGENTA + Style.BRIGHT}Max Delay For Each Game -> {Style.RESET_ALL}").strip())
                if max_delay >= min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Max Delay must be >= Min Delay.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
         
    async def print_timer(self, min_delay: int, max_delay: int, message: str):
        for remaining in range(random.randint(min_delay, max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For {message}...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_question(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Deposit IRYS{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Withdraw IRYS{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Play Snake Game{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}4. Play Asteroids Game{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}5. Play Hexshot Game{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}6. Play Missile Game{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}7. Run All Features{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3/4/5/6/7] -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3, 4, 5, 6, 7]:
                    option_type = (
                        "Deposit IRYS" if option == 1 else 
                        "Withdraw IRYS" if option == 2 else 
                        "Play Snake Game" if option == 3 else 
                        "Play Asteroids Game" if option == 4 else 
                        "Play Hexshot Game" if option == 5 else 
                        "Play Missile Game" if option == 6 else 
                        "Run All Features"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{option_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, 3, 4, 5, 6, or 7.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, 3, 4, 5, 6, or 7).{Style.RESET_ALL}")

        if option == 1:
            self.print_deposit_question()

        if option == 2:
            self.print_withdraw_question()

        if option == 3:
            self.print_game_count_question("Snake")
            self.print_delay_question()

        if option == 4:
            self.print_game_count_question("Asteroids")
            self.print_delay_question()

        if option == 5:
            self.print_game_count_question("Hexshot")
            self.print_delay_question()

        if option == 6:
            self.print_game_count_question("Missile")
            self.print_delay_question()

        elif option == 7:
            self.print_bank_question()
            self.print_game_count_question("Snake")
            self.print_game_count_question("Asteroids")
            self.print_game_count_question("Hexshot")
            self.print_game_count_question("Missile")
            self.print_delay_question()

        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 2 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return option, proxy_choice, rotate_proxy
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=10)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    async def start_game(self, account: str, address: str, game_id: str, score: int, start_timestamp: int, game_type: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/game/start"
        data = json.dumps(self.generate_game_payload(account, address, game_id, score, start_timestamp, game_type, "Start"))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
                return None
        
    async def complete_game(self, account: str, address: str, game_id: str, score: int, start_timestamp: int, game_type: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/game/complete"
        data = json.dumps(self.generate_game_payload(account, address, game_id, score, start_timestamp, game_type, "Complete"))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
                return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy    :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue

                return False
            
            return True
        
    async def process_perform_deposit(self, account: str, address: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_deposit(account, address, use_proxy)
        if tx_hash and block_number:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}                      "
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_withdraw(self, account: str, address: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_withdraw(account, address, use_proxy)
        if tx_hash and block_number:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}                      "
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_option_1(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Deposit  :{Style.RESET_ALL}                      ")

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.deposit_amount} IRYS {Style.RESET_ALL}"
        )

        balance = await self.get_token_balance(address, self.NATIVE_TOKEN_ADDRESS, use_proxy)
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} IRYS {Style.RESET_ALL}"
        )

        if balance is None:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Fetch IRYS Token Balance Failed {Style.RESET_ALL}"
            )
            return

        if balance <= self.deposit_amount:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient IRYS Token Balance {Style.RESET_ALL}"
            )
            return
        
        await self.process_perform_deposit(account, address, use_proxy)

    async def process_option_2(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Withdraw :{Style.RESET_ALL}                      ")

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.withdraw_amount} IRYS {Style.RESET_ALL}"
        )

        balance = await self.get_token_balance(address, self.ARCADE_BANK_ADDRESS, use_proxy)
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} IRYS {Style.RESET_ALL}"
        )

        if balance is None:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Fetch IRYS Token Balance From Arcade Bank Failed {Style.RESET_ALL}"
            )
            return

        if balance < self.withdraw_amount:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient IRYS Token Balance From Arcade Bank {Style.RESET_ALL}"
            )
            return
        
        await self.process_perform_withdraw(account, address, use_proxy)

    async def process_option_3(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Snake    :{Style.RESET_ALL}                                   ")

        for i in range(self.snake_game_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT}Game{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {i+1} {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}Of{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.snake_game_count} {Style.RESET_ALL}                                   "
            )

            game_id = self.generate_random_string()
            start_timestamp = int(time.time()) * 1000
            game_type = "snake"
            score = 1000

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Id  :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} game_{start_timestamp}_{game_id} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Cost:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} 0.001 IRYS {Style.RESET_ALL}"
            )

            balance = await self.get_token_balance(address, self.ARCADE_BANK_ADDRESS, use_proxy)
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} IRYS {Style.RESET_ALL}"
            )

            if balance is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch IRYS Token Balance From Arcade Bank Failed {Style.RESET_ALL}"
                )
                continue

            if balance < 0.001:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient IRYS Token Balance From Arcade Bank {Style.RESET_ALL}"
                )
                return

            start = await self.start_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
            if not start: 
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Starting Game Failed {Style.RESET_ALL}"
                )
                continue


            if start and start.get("success"):
                message = start.get("message")
                block_number = start.get("data", {}).get("blockNumber")
                tx_hash = start.get("data", {}).get("transactionHash")

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                )
                await self.print_timer(25, 30, "Game Completion")

                complete = await self.complete_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
                if not complete: 
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Completing Game Failed {Style.RESET_ALL}"
                    )
                    continue

                if complete and complete.get("success"):
                    message = complete.get("message")
                    reward = complete.get("data", {}).get("rewardAmount")
                    block_number = complete.get("data", {}).get("blockNumber")
                    tx_hash = complete.get("data", {}).get("transactionHash")

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}                                   "
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Score    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {score} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Reward   :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {reward} IRYS {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                    )

                else:
                    err_msg = complete.get("message")
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                    )

            else:
                err_msg = start.get("message")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                )

            await self.print_timer(self.min_delay, self.max_delay, "Next Game")

    async def process_option_4(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Asteroids:{Style.RESET_ALL}                                   ")

        for i in range(self.asteroids_game_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT}Game{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {i+1} {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}Of{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.asteroids_game_count} {Style.RESET_ALL}                                   "
            )

            game_id = self.generate_random_string()
            start_timestamp = int(time.time()) * 1000
            game_type = "asteroids"
            score = 500000

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Id  :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} game_{start_timestamp}_{game_id} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Cost:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} 0.001 IRYS {Style.RESET_ALL}"
            )

            balance = await self.get_token_balance(address, self.ARCADE_BANK_ADDRESS, use_proxy)
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} IRYS {Style.RESET_ALL}"
            )

            if balance is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch IRYS Token Balance From Arcade Bank Failed {Style.RESET_ALL}"
                )
                continue

            if balance < 0.001:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient IRYS Token Balance From Arcade Bank {Style.RESET_ALL}"
                )
                return

            start = await self.start_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
            if not start: 
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Starting Game Failed {Style.RESET_ALL}"
                )
                continue

            if start and start.get("success"):
                message = start.get("message")
                block_number = start.get("data", {}).get("blockNumber")
                tx_hash = start.get("data", {}).get("transactionHash")

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                )
                await self.print_timer(25, 30, "Game Completion")

                complete = await self.complete_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
                if not complete: 
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Completing Game Failed {Style.RESET_ALL}"
                    )
                    continue

                if complete and complete.get("success"):
                    message = complete.get("message")
                    reward = complete.get("data", {}).get("rewardAmount")
                    block_number = complete.get("data", {}).get("blockNumber")
                    tx_hash = complete.get("data", {}).get("transactionHash")

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}                                   "
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Score    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {score} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Reward   :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {reward} IRYS {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                    )

                else:
                    err_msg = complete.get("message")
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                    )
                    
            else:
                err_msg = start.get("message")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                )

            await self.print_timer(self.min_delay, self.max_delay, "Next Game")

    async def process_option_5(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Hexshot  :{Style.RESET_ALL}                                   ")

        for i in range(self.hexshot_game_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT}Game{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {i+1} {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}Of{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.hexshot_game_count} {Style.RESET_ALL}                                   "
            )

            game_id = self.generate_random_string()
            start_timestamp = int(time.time()) * 1000
            game_type = "hex-shooter"
            score = 65000

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Id  :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} game_{start_timestamp}_{game_id} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Cost:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} 0.001 IRYS {Style.RESET_ALL}"
            )

            balance = await self.get_token_balance(address, self.ARCADE_BANK_ADDRESS, use_proxy)
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} IRYS {Style.RESET_ALL}"
            )

            if balance is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch IRYS Token Balance From Arcade Bank Failed {Style.RESET_ALL}"
                )
                continue

            if balance < 0.001:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient IRYS Token Balance From Arcade Bank {Style.RESET_ALL}"
                )
                return

            start = await self.start_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
            if not start: 
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Starting Game Failed {Style.RESET_ALL}"
                )
                continue

            if start and start.get("success"):
                message = start.get("message")
                block_number = start.get("data", {}).get("blockNumber")
                tx_hash = start.get("data", {}).get("transactionHash")

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                )
                await self.print_timer(25, 30, "Game Completion")

                complete = await self.complete_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
                if not complete: 
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Completing Game Failed {Style.RESET_ALL}"
                    )
                    continue

                if complete and complete.get("success"):
                    message = complete.get("message")
                    reward = complete.get("data", {}).get("rewardAmount")
                    block_number = complete.get("data", {}).get("blockNumber")
                    tx_hash = complete.get("data", {}).get("transactionHash")

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}                                   "
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Score    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {score} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Reward   :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {reward} IRYS {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                    )

                else:
                    err_msg = complete.get("message")
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                    )
                    
            else:
                err_msg = start.get("message")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                )

            await self.print_timer(self.min_delay, self.max_delay, "Next Game")

    async def process_option_6(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Missile  :{Style.RESET_ALL}                                   ")

        for i in range(self.missile_game_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT}Game{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {i+1} {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}Of{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.missile_game_count} {Style.RESET_ALL}                                   "
            )

            game_id = self.generate_random_string()
            start_timestamp = int(time.time()) * 1000
            game_type = "missile-command"
            score = 1600000

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Id  :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} game_{start_timestamp}_{game_id} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Game Cost:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} 0.001 IRYS {Style.RESET_ALL}"
            )

            balance = await self.get_token_balance(address, self.ARCADE_BANK_ADDRESS, use_proxy)
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} IRYS {Style.RESET_ALL}"
            )

            if balance is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch IRYS Token Balance From Arcade Bank Failed {Style.RESET_ALL}"
                )
                continue

            if balance < 0.001:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient IRYS Token Balance From Arcade Bank {Style.RESET_ALL}"
                )
                return

            start = await self.start_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
            if not start: 
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Starting Game Failed {Style.RESET_ALL}"
                )
                continue

            if start and start.get("success"):
                message = start.get("message")
                block_number = start.get("data", {}).get("blockNumber")
                tx_hash = start.get("data", {}).get("transactionHash")

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                )
                await self.print_timer(25, 30, "Game Completion")

                complete = await self.complete_game(account, address, game_id, score, start_timestamp, game_type, use_proxy)
                if not complete: 
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Completing Game Failed {Style.RESET_ALL}"
                    )
                    continue

                if complete and complete.get("success"):
                    message = complete.get("message")
                    reward = complete.get("data", {}).get("rewardAmount")
                    block_number = complete.get("data", {}).get("blockNumber")
                    tx_hash = complete.get("data", {}).get("transactionHash")

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}                                   "
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Score    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {score} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Reward   :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {reward} IRYS {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
                    )

                else:
                    err_msg = complete.get("message")
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                    )
                    
            else:
                err_msg = start.get("message")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}                                   "
                )

            await self.print_timer(self.min_delay, self.max_delay, "Next Game")

    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            try:
                web3 = await self.get_web3_with_check(address, use_proxy)
            except Exception as e:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Web3 Not Connected {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                return
            
            self.used_nonce[address] = web3.eth.get_transaction_count(address, "pending")
 
            if option == 1:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option   :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Deposit IRYS {Style.RESET_ALL}"
                )
                await self.process_option_1(account, address, use_proxy)

            elif option == 2:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option   :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Withdraw IRYS {Style.RESET_ALL}"
                )
                await self.process_option_2(account, address, use_proxy)

            elif option == 3:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option   :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Play Snake Game {Style.RESET_ALL}"
                )
                await self.process_option_3(account, address, use_proxy)

            elif option == 4:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option   :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Play Asteroids Game {Style.RESET_ALL}"
                )
                await self.process_option_4(account, address, use_proxy)

            elif option == 5:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option   :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Play Hexshot Game {Style.RESET_ALL}"
                )
                await self.process_option_5(account, address, use_proxy)

            elif option == 6:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option   :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Play Missile Game {Style.RESET_ALL}"
                )
                await self.process_option_6(account, address, use_proxy)

            elif option == 7:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option   :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Run All Features {Style.RESET_ALL}"
                )

                if self.bank_option == 1:
                    await self.process_option_1(account, address, use_proxy)
                elif self.bank_option == 2:
                    await self.process_option_2(account, address, use_proxy)
            
                await self.process_option_3(account, address, use_proxy)
                await self.process_option_4(account, address, use_proxy)
                await self.process_option_5(account, address, use_proxy)
                await self.process_option_6(account, address, use_proxy)

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            option, proxy_choice, rotate_proxy = self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                use_proxy = True if proxy_choice == 1 else False
                if use_proxy:
                    await self.load_proxies()
                
                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)

                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status   :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        self.HEADERS[address] = {
                            "Accept": "*/*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://play.irys.xyz",
                            "Referer": "https://play.irys.xyz/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-origin",
                            "User-Agent": FakeUserAgent().random
                        }

                        await self.process_accounts(account, address, option, use_proxy, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Irys()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Irys Game - BOT{Style.RESET_ALL}                                       "                              
        )
