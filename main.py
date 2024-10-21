import os
import logging
import time
from web3 import Web3
from web3.exceptions import InvalidAddress, ContractLogicError
from dotenv import load_dotenv

load_dotenv()

# Custom log level for SUCCESS
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.success = success

# Logging setup
log_format = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# Environment variables
provider_url = os.getenv('PROVIDER_URL')
private_key = os.getenv('PRIVATE_KEY')
contract_address = os.getenv('CONTRACT_ADDRESS')

if not provider_url or not private_key or not contract_address:
    raise ValueError("Lütfen .env dosyanızın içerisinde PRIVATE_KEY belirleyin. Diğer değişkenleri değiştirmeniz önerilmez.")

# Web3 setup
web3 = Web3(Web3.HTTPProvider(provider_url))
account = web3.eth.account.from_key(private_key)
contract_address = web3.to_checksum_address(contract_address)

# Method ID for claim() function
method_id = "0x4e71d92d"
gas_limit = 300000
gas_price = web3.eth.gas_price

def claimable_frag():
    try:
        data = f"0x89885049000000000000000000000000{account.address[2:]}"
        from_address = web3.to_checksum_address('0x24edfad36015420a84573684644f6dc74f0ba8c5')
        response = web3.eth.call({
            'from': from_address,
            'to': contract_address,
            'data': data,
        })
        fragment_count = int(response.hex(), 16)
        logger.info(f"Fragment sayısı: {fragment_count}")
        return fragment_count
    except Exception as e:
        logger.error(f"Fragment sayısı belirlenirken hata oluştu: {e}")
        raise

def claim():
    try:
        logger.info("Claim işlemi yapılıyor..")
        nonce = web3.eth.get_transaction_count(account.address)
        tx = {
            'from': account.address,
            'to': contract_address,
            'nonce': nonce,
            'gas': gas_limit,
            'gasPrice': web3.utils.toHex(gas_price),
            'data': method_id
        }
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.success(f"İşlem Onaylandı: {receipt.transactionHash.hex()}")
        return receipt.transactionHash.hex()
    except Exception as e:
        logger.error(f"Claim işlemi gerçekleştirilirken hata oluştu: {e}")
        raise

def runforestrun():
    try:
        while True:
            while claimable_frag() > 0:
                try:
                    claim()
                    time.sleep(15)
                except ContractLogicError as e:
                    logger.error(f"Kontrat Çağrı Hatası: {e}")
                except InvalidAddress as e:
                    logger.error(f"Geçersiz Adres Hatası: {e}")
                except Exception as e:
                    logger.error(f"Claim İşlemi Sırasında Hata: {e}")
            logger.info("Claim edilebilir Fragment sayısı şu an 0, 12 saat sonra otomatik olarak yeniden denenecek..")
            time.sleep(12 * 60 * 60)
    except Exception as e:
        logger.error(f"Python Dosyası Çalıştırma Hatası: {e}")
        raise


if __name__ == "__main__":
    runforestrun()
