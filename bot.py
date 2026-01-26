"""
bot 
    run this bot help you query the stock and place order via shioaji (永豐證券 api)
    talk to you bot

    ASK:
        2330 2377
        will return the current of 2330 and 2377

    BUY: (keyword: 買, Buy, BUY, buy)
        買進 2330 10@1700
        or
        買入 2330 10@1700
        or 
        買 2330 10@1700
        or
        Buy 2330 10@1700
        or
        buy 2330 10@1700

        will place order for 2330 buy 10 shares at 1700.00

        買進 0050 1100@72.15
        or
        買入 0050 1100@72.15
        or
        狂買 0050 1100@72.15
        or
        buy 0050 1100@72.15

        the shares are more than 1000, would place order 張 for 0050 buy 1 張  at 72.15

    SELL: (keyword: 賣, Sell, SELL, sell)
        follow the same rule with BUY

    envioment variable

    TG_USERNAME = os.getenv('TG_USERNAME')              # your telegram username, only this username allow to talk with you
    TG_TOKEN  = os.getenv('TG_TOKEN')                   # telegram bot api token 
    CA_PATH = os.getenv('CA_PATH') or "./sinopac.pfx"   # https://ai.sinotrade.com.tw/python/Main/index.aspx
    CA_PASSWD = os.getenv("CA_PASSWD")                  # certificate password
    API_KEY = os.getenv("API_KEY")                      # API Key 
    API_SECRET = os.getenv("API_SECRET")                # Secret Key

"""
import logging, os, sys
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import shioaji as sj
load_dotenv()

TG_USERNAME = os.getenv('TG_USERNAME')              # your telegram username, only this username allow to talk with you
TG_TOKEN  = os.getenv('TG_TOKEN')                   # telegram bot api token 
CA_PATH = os.getenv('CA_PATH') or "./sinopac.pfx"   # https://ai.sinotrade.com.tw/python/Main/index.aspx
CA_PASSWD = os.getenv("CA_PASSWD")                  # certificate password
API_KEY = os.getenv("API_KEY")                      # API Key 
API_SECRET = os.getenv("API_SECRET")                # Secret Key
DEBUG = os.getenv("DEBUG")                          # debug boolean

if not all([TG_USERNAME, TG_TOKEN, CA_PATH, CA_PASSWD, API_KEY, API_SECRET]):
    print(__doc__)
    sys.exit(0)

# logging
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Running bot in DEBUG mod")
    sjapi = sj.Shioaji(simulation=True)
else:
    logging.basicConfig(level=logging.INFO)
    logging.info("Running bot in 💰💰💰💰💰💰💰💰 REAL MONEY 💰💰💰💰💰💰💰💰")
    sjapi = sj.Shioaji()

logger = logging.getLogger(__name__)

# sjapi.activate_ca(ca_path=CA_PATH, ca_passwd=CA_PASSWD, person_id=CA_PASSWD)
accounts =  sjapi.login(API_KEY, API_SECRET)
sjapi.activate_ca(ca_path=CA_PATH, ca_passwd=CA_PASSWD)
logger.debug(f'signed in SinoPac with {accounts}')

class CMD:
    """action  (string) => BUY, SELL, ASK
     stock ([]string) => ["0050"]
     shares  (integr) => 1 the unit is 1 share, 1000 一張
     price   (float) 0
     price shares format 100@70.21 => shares 100 at price 70.21
     """

    action = 'ASK'
    stock = []
    price = 0.0
    shares = 0
    cmd_string = ''
    share_word = ''
    cmd_slice = []

    def __init__(self, cmd=''):

        self.cmd_string = cmd
        self.cmd_slice = [s.strip() for s in cmd.split(" ")]
        stock_list = []

        #find the shares@price
        for one in self.cmd_slice:
            if '@' in one:
                share_slice = one.split('@')
                if len(share_slice) != 2:
                    break
                
                shares_str = share_slice[0]
                price_str = share_slice[1]
                try:
                    self.price = float(price_str)
                except:
                    break
                
                # shares and price is ok
                if shares_str.isdigit() and self.price > 0:
                    # found shares@price
                    self.share_word = one
                    self.shares = int(shares_str)
                break
        # test buy or sell
        match cmd:
            case  cmd if any(word in cmd for word in ['buy', 'Buy', 'BUY', '買']):
                self.action = "BUY"
            case  cmd if any(word in cmd for word in ['sell', 'Sell', 'SELL', '賣']):
                self.action = "SELL"
            case _:
                pass

        # find the one stock id 
        for one in self.cmd_slice:
            re_stocks = re.findall(r"^\d{3,6}$", one)
            if len(re_stocks) == 1:
                stock_list.append(re_stocks[0].strip())
        if len(stock_list) > 0:
            self.stock = stock_list

    def __str__(self):
        return f'<CMD action:{self.action}, stock:"{self.stock}" {self.shares} shares at {self.price}>'

def ask(cmd):
    reply_list = []
    contracts = [] 
    for stockID in cmd.stock:
        contract = sjapi.Contracts.Stocks[stockID]
        if contract:
            contracts.append(contract)

    if len(contracts) == 0: 
        return ""

    snapshots = sjapi.snapshots(contracts)

    if len(snapshots) == len(contracts):
        # [Snapshot( ts=1769088600000000000, code='2377', exchange='TSE', open=101.0, high=103.0, low=100.5, close=101.0,
        #    tick_type=<TickType.Sell: 'Sell'>, change_price=1.3, change_rate=1.3, change_type=<ChangeType.Up: 'Up'>,
        #    average_price=101.54, volume=307, total_volume=6596, amount=31007000, total_amount=669805000, yesterday_volume=6626.0,
        #    buy_price=100.5, buy_volume=490.0, sell_price=101.5, sell_volume=65, volume_ratio=1.0)]
        for idx, s in enumerate(snapshots):
            c = contracts[idx]
            line = f'{c.name} {s.code} $ {s.close} ({s.change_price})\n量: {s.total_volume} ({s.yesterday_volume} 昨)\n買: {s.buy_price} ({s.buy_volume}) 賣: {s.sell_price} ({s.sell_volume})\n++++++'
            reply_list.append(line)
     
    return "\n".join(reply_list)

def place_order(cmd):
    sheets = 0
    reply_list = []
    contract = None 
    cmd_action = None
    action_word = None

    if len(cmd.stock) != 1:
        return "股票代碼有問題啦"

    contract = sjapi.Contracts.Stocks[cmd.stock[0]]
    if not contract:
        return "股票代碼有問題啦"

    if cmd.price <= 0:
        return "價格有問題啦"

    if cmd.shares <= 0:
        return "股數有問題啦"

    if cmd.shares >= 1000:
        sheets = cmd.shares // 1000
    

    match cmd.action:
        case  "BUY":
            cmd_action = sj.constant.Action.Buy
            action_word = "買進"
        case "SELL":
            cmd_action = sj.constant.Action.Sell
            action_word = "賣出"

    if sheets > 0:
        # use sheets
        reply_list.append(f'{action_word}股數可以湊張，{action_word} {contract.name} {contract.code} {sheets} 張')
        order = sjapi.Order(
                  price=cmd.price,
                  quantity=sheets,
                  action=cmd_action,
                  price_type=sj.constant.StockPriceType.LMT,
                  order_type=sj.constant.OrderType.ROD,
                  order_lot=sj.constant.StockOrderLot.Common,
                  account=sjapi.stock_account,
              )
        trade = sjapi.place_order(contract, order)
        sjapi.update_status()
        logger.info(f'trade: {trade}')
        if trade and trade.status and trade.status.status:
            reply_list.append(f'單據狀態 {trade.status.status} {trade.status.msg}')

    else:
        # use shares
        reply_list.append(f'{action_word} {contract.name} {contract.code} {cmd.shares} 股')
        order = sjapi.Order(
                  price=cmd.price,
                  quantity=cmd.shares,
                  action=cmd_action,
                  price_type=sj.constant.StockPriceType.LMT,
                  order_type=sj.constant.OrderType.ROD,
                  order_lot=sj.constant.StockOrderLot.IntradayOdd,
                  account=sjapi.stock_account,
              )
        trade = sjapi.place_order(contract, order)
        sjapi.update_status()
        logger.info(f'trade: {trade}')
        if trade and trade.status and trade.status.status:
            reply_list.append(f'單據狀態 {trade.status.status} {trade.status.msg}')

    return "\n".join(reply_list)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # debug
    logger.info(f'update: {update}')

    # only allow to myself
    if not update.message or not update.message.chat or update.message.chat.username != TG_USERNAME :
        await update.message.reply_text(f'{update.effective_user.first_name} not allow to talk')
        return
    
    # ignore empty text message
    if not update.message.text:
        return

    cmd_result = CMD(update.message.text)

    # no valid stock
    if len(cmd_result.stock) == 0:
        return
    
    logger.info(f'{cmd_result}')
    reply_text = ''
    match cmd_result.action:
        case  "ASK":
            print("ASK")
            reply_text = ask(cmd_result)
        case  "BUY":
            print("BUY")
            reply_text = place_order(cmd_result)
        case "SELL":
            print("SELL")
            reply_text = place_order(cmd_result)
   
    if reply_text != "":
        await update.message.reply_text(f'{reply_text}')


if __name__ == '__main__':
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, start))
    app.run_polling()
