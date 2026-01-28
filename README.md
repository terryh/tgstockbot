## 永豐金證券 telegram API 交易機器人

一個利用 telegram bot api 及 永豐金證券 api 聊天下單交易的機器人，
在盤中您可以利用和他對話的方式，下買賣單，他會自動判斷，零股或是整張的下單方式，
沒有支援當日沖，沒有融資，融卷的單，都是現金的買賣單，一個簡單的實作應用，
指令必須用空格隔開，單位都是股數，沒有張的單位，下超過一張的股數，只會下整數的張數。

所有買賣單，委託類別 ROD ，當日有效，價格 LMT ，限價單


example: 

買進 0050 100股 價格 72.5
```
買 0050 100@72.5
```

買進 0050 1張 價格 72.5
```
買 0050 1000@72.5
```

賣 0050 100股 價格 76
```
賣 0050 100@76
```

賣 0050 1張 價格 76
```
賣 0050 1000@76
```

查 0050 2330 報價
```
0050 2330
```

## 安裝與設定


### 建立 telegram bot api

建立 telegram bot  [https://core.telegram.org/bots#how-do-i-create-a-bot](https://core.telegram.org/bots#how-do-i-create-a-bot)


### 永豐金證券的 API

建立 api [https://ai.sinotrade.com.tw/python/Main/index.aspx](https://ai.sinotrade.com.tw/python/Main/index.aspx)

### 設定環境


* 安裝 python 請搜尋網路，或是參考官方文件

* 將程式由 github 上面抓取下來

* 安裝相依套件，指令

```
pip install -r requirements.txt
```

* 設定環境變數，請複製 dot.env 檔案為 .env，修改內容

.env 範例
```
TG_TOKEN=1234567:AA_bb #您的 telegram bot api
TG_USERNAME=stocktw    #您的 telegram 帳號 (只有這個帳號可以跟他說話)
CA_PATH=./sinopac.pfx  #您的永豐金證券 api 的憑證檔案，預設名稱是 ./sinopac.pfx)
CA_PASSWD=A123456789   #憑證檔案密碼 (預設是您的身分證字號英文大寫)
API_KEY=API_Keyeeee    #永豐金證券 API KEY
API_SECRET=API_Seee    #永豐金證券 API SECRET
DEBUG=true             #這個值有設定的話，下單使用模擬單，這一行刪除，執行就是正式單
```

### 執行

正式單

```
python bot.py
```

模擬單，DEBUG 可以設定在 .env 檔案中，或是直接給

```
DEBUG=true python bot.py
```

## 結語

單純簡單的下現金單的機制驗證，可以有很多延伸，例如


* 同券商，多帳號，串接，同時下單

* 多個不同使用者，連接獨立的帳號，用群聊的方式，各自下自己獨立的單，但是因為是群聊，所以變成，可以容易跟單，大家一起玩感覺很熱血

* 多家不同證券商串接，同時下單

* 邊聊天，邊投資

## 警語

投資一定有風險，投資前應審慎評估。投資人應詳閱公開說明書，且過往績效不代表未來表現。所有投資工具（包括股票、基金、ETF）皆有賺有賠，最大可能損失所有本金，且不保證收益。防範詐騙，切勿信「保證獲利」或提供個資。 
