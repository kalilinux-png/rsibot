import datetime as dt
import time
import yfinance as yf
from ks_api_client import ks_api
import pandas_ta as ta
import json
import requests
from fastapi import FastAPI
app=FastAPI(debug=True,version="1.0")


class Autobot:

    def __init__(self):
        pass
        self.__access_token = None
        self.__password = None
        self.__consumer_key = None
        self.__userid = None
        self.__appid = None
        self.shubh = None

    def login(self, consumer_key, access_token, app_id, user_id, password, ip='127.0.0.1'):
        self.shubh = ks_api.KSTradeApi(
            access_token, user_id, consumer_key, ip, app_id)
        headers = {'accept': 'application/json', 'consumerKey': consumer_key, 'ip': '127.0.0.1',
                   'appId': app_id, 'Content-Type': 'application/json', 'Authorization': "Bearer "+access_token}
        data = json.dumps({'userid': user_id, 'password': password})
        response = requests.post(
            "https://tradeapi.kotaksecurities.com/apim/session/1.0/session/login/userid", headers=headers, data=data).json()
        url = "https://tradeapi.kotaksecurities.com/apim/session/1.0/session/2FA/oneTimeToken"
        headers["oneTimeToken"] = response['Success']['oneTimeToken']
        self.shubh.one_time_token = headers['oneTimeToken']
        data = json.dumps({"userid": user_id})
        resp = requests.post(url, headers=headers, data=data).json()
        self.shubh.session_token = resp['success']['sessionToken']
        print("Loged In  Successfully")
        return self.shubh

    def ltp(self, code):
        '''Returns Ltp in form of float'''
        return float(self.shubh.quote(code, 'LTP')['success'][0]['lastPrice'])

    def ask_bid(self, name):
        '''Returns ask bid in form of buy,buy_q,sell,sell_q'''

        data = self.shubh.quote(name, 'DEPTH')['success']['depth'][0]

        buy = data['buy'][0]

        sell = data['sell'][0]

        return float(buy['price']), float(buy['quantity']), float(sell['price']), float(sell['quantity'])

    def place_order(self, type='None', instrument_token=None, quantity=1, price=0, trigger_price=0, validity='GFD', tag=''):

        type = type.upper()

        # change's are made from this refernce list(place_order('buy', code, price=buy_price, quantity=quantity,tag='')[
        #          'Success'].values())[0]

        order_details = list(self.shubh.place_order(order_type="N", instrument_token=instrument_token, transaction_type=type,
                                                    quantity=quantity, price=price, disclosed_quantity=0, trigger_price=trigger_price, validity=validity, tag=tag)['Success'].values())[0]
        # winsound.Beep(3279, 100) if type == 'BUY' else winsound.Beep(2323, 100)

        return order_details

    def order_status(self, order_Id):
        ''' This Function Is Used To Get Order Status Like Pending Or Traded ['staus'] == TRAD OR OPN OR CAN ['statusMessage']==Open or Completely Traded Order'''

        return self.shubh.order_report(order_Id)['success'][-1]['status']

    def get_rsi(self, stock_name="VEDL.NS", days=7):
        """To Get Rsi Value for a stock """
        now = dt.datetime.now()
        start_date = dt.datetime(
            year=now.year, month=now.month, day=now.day, hour=9, minute=15)
        start_date = start_date+dt.timedelta(days=-days)
        week1 = yf.Ticker(stock_name).history(
            period="1d", interval="5m", start=start_date, prepost=True)
        week1['rsi'] = ta.rsi(week1.Close, length=9, drift=2)
        rsi = week1.rsi.tail(1).iloc[-1]
        return rsi

    def evaluate(self, stock_name,exchange="NS"):
        rsi=self.get_rsi(stock_name=stock_name+"."+exchange)
        print(rsi)
        stock_code = requests.get(
            f"https://googleoauthentication.herokuapp.com/code/nse/{stock_name}").json()
        # stock_code= 1909
        print(stock_code)
        Buy_order = False
        Sell_order = False
        while True:
            print("inside loop",rsi,Buy_order,Sell_order)
            if rsi <= 30 and not Buy_order:
                # place Buy order if rsi <= 30 and no Buy Order was placed Earlier
                order_details = self.place_order(
                    'buy', instrument_token=int(stock_code))
                print("Buy Order Placed",order_details)
                Buy_order=True
                Sell_order=False
            elif rsi >= 70 and not Sell_order:
                # place Sell  order if rsi <= 30 and no Sell  Order was placed Earlier
                order_details = self.place_order(
                    'sell', instrument_token=int(stock_code))
                print("Sell Order Placed",order_details)
                Sell_order=True
                Buy_order=False




if __name__ == "__main__":

    access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1XUTVObVJoTVdJM1pUVXdPVFEwTURNd1l6WXlaVGN6TUdSallXWXlZVGRrWVdRM05XUTFOQT09In0.eyJhdWQiOiJodHRwOlwvXC9vcmcud3NvMi5hcGltZ3RcL2dhdGV3YXkiLCJzdWIiOiJTWTIzMDEyMDAzQGNhcmJvbi5zdXBlciIsImFwcGxpY2F0aW9uIjp7Im93bmVyIjoiU1kyMzAxMjAwMyIsInRpZXJRdW90YVR5cGUiOiJyZXF1ZXN0Q291bnQiLCJ0aWVyIjoiVW5saW1pdGVkIiwibmFtZSI6Im1haW4iLCJpZCI6MjMxNCwidXVpZCI6bnVsbH0sInNjb3BlIjoiYW1fYXBwbGljYXRpb25fc2NvcGUgZGVmYXVsdCIsImlzcyI6Imh0dHBzOlwvXC90cmFkZWFwaS5rb3Rha3NlY3VyaXRpZXMuY29tOjQ0M1wvb2F1dGgyXC90b2tlbiIsInRpZXJJbmZvIjp7IjYwcGVyTWluIjp7InRpZXJRdW90YVR5cGUiOiJyZXF1ZXN0Q291bnQiLCJzdG9wT25RdW90YVJlYWNoIjp0cnVlLCJzcGlrZUFycmVzdExpbWl0IjoxLCJzcGlrZUFycmVzdFVuaXQiOiJzZWMifSwiVW5saW1pdGVkIjp7InRpZXJRdW90YVR5cGUiOiJyZXF1ZXN0Q291bnQiLCJzdG9wT25RdW90YVJlYWNoIjp0cnVlLCJzcGlrZUFycmVzdExpbWl0IjowLCJzcGlrZUFycmVzdFVuaXQiOm51bGx9fSwia2V5dHlwZSI6IlBST0RVQ1RJT04iLCJzdWJzY3JpYmVkQVBJcyI6W3sic3Vic2NyaWJlclRlbmFudERvbWFpbiI6ImNhcmJvbi5zdXBlciIsIm5hbWUiOiJQb3J0Zm9saW8tQVBJIiwiY29udGV4dCI6IlwvYXBpbVwvcG9ydGZvbGlvXC8xLjAiLCJwdWJsaXNoZXIiOiJhZG1pbiIsInZlcnNpb24iOiIxLjAiLCJzdWJzY3JpcHRpb25UaWVyIjoiVW5saW1pdGVkIn0seyJzdWJzY3JpYmVyVGVuYW50RG9tYWluIjoiY2FyYm9uLnN1cGVyIiwibmFtZSI6IlJlcG9ydHMtS1NFQyIsImNvbnRleHQiOiJcL2FwaW1cL3JlcG9ydHNcLzEuMCIsInB1Ymxpc2hlciI6ImFkbWluIiwidmVyc2lvbiI6IjEuMCIsInN1YnNjcmlwdGlvblRpZXIiOiJVbmxpbWl0ZWQifSx7InN1YnNjcmliZXJUZW5hbnREb21haW4iOiJjYXJib24uc3VwZXIiLCJuYW1lIjoiU2Vzc2lvbi1BUEkiLCJjb250ZXh0IjoiXC9hcGltXC9zZXNzaW9uXC8xLjAiLCJwdWJsaXNoZXIiOiJhZG1pbiIsInZlcnNpb24iOiIxLjAiLCJzdWJzY3JpcHRpb25UaWVyIjoiVW5saW1pdGVkIn0seyJzdWJzY3JpYmVyVGVuYW50RG9tYWluIjoiY2FyYm9uLnN1cGVyIiwibmFtZSI6IlBvc2l0aW9ucy1BUEkiLCJjb250ZXh0IjoiXC9hcGltXC9wb3NpdGlvbnNcLzEuMCIsInB1Ymxpc2hlciI6ImFkbWluIiwidmVyc2lvbiI6IjEuMCIsInN1YnNjcmlwdGlvblRpZXIiOiI2MHBlck1pbiJ9LHsic3Vic2NyaWJlclRlbmFudERvbWFpbiI6ImNhcmJvbi5zdXBlciIsIm5hbWUiOiJPcmRlcnMtQVBJIiwiY29udGV4dCI6IlwvYXBpbVwvb3JkZXJzXC8xLjAiLCJwdWJsaXNoZXIiOiJhZG1pbiIsInZlcnNpb24iOiIxLjAiLCJzdWJzY3JpcHRpb25UaWVyIjoiVW5saW1pdGVkIn0seyJzdWJzY3JpYmVyVGVuYW50RG9tYWluIjoiY2FyYm9uLnN1cGVyIiwibmFtZSI6IlNjcmlwTWFzdGVyLUFQSSIsImNvbnRleHQiOiJcL2FwaW1cL3NjcmlwbWFzdGVyXC8xLjEiLCJwdWJsaXNoZXIiOiJhZG1pbiIsInZlcnNpb24iOiIxLjEiLCJzdWJzY3JpcHRpb25UaWVyIjoiVW5saW1pdGVkIn0seyJzdWJzY3JpYmVyVGVuYW50RG9tYWluIjoiY2FyYm9uLnN1cGVyIiwibmFtZSI6IldhdGNobGlzdC1BUEkiLCJjb250ZXh0IjoiXC9hcGltXC93YXRjaGxpc3RcLzIuMSIsInB1Ymxpc2hlciI6ImFkbWluIiwidmVyc2lvbiI6IjIuMSIsInN1YnNjcmlwdGlvblRpZXIiOiJVbmxpbWl0ZWQifSx7InN1YnNjcmliZXJUZW5hbnREb21haW4iOiJjYXJib24uc3VwZXIiLCJuYW1lIjoiTWFyZ2lucy1BUEkiLCJjb250ZXh0IjoiXC9hcGltXC9tYXJnaW5cLzEuMCIsInB1Ymxpc2hlciI6ImFkbWluIiwidmVyc2lvbiI6IjEuMCIsInN1YnNjcmlwdGlvblRpZXIiOiJVbmxpbWl0ZWQifSx7InN1YnNjcmliZXJUZW5hbnREb21haW4iOiJjYXJib24uc3VwZXIiLCJuYW1lIjoiUXVvdGVzLUtTRUMiLCJjb250ZXh0IjoiXC9hcGltXC9xdW90ZXNcL3YxLjAiLCJwdWJsaXNoZXIiOiJhZG1pbiIsInZlcnNpb24iOiJ2MS4wIiwic3Vic2NyaXB0aW9uVGllciI6IlVubGltaXRlZCJ9XSwiY29uc3VtZXJLZXkiOiJyZFpDRzBWUEFGb1hrOUdmU1pwUE5mNFppZ1VhIiwiZXhwIjozNzc2Njk4OTA0LCJpYXQiOjE2MjkyMTUyNTcsImp0aSI6ImFjNjE5Y2Y5LTlkZGItNDIzMS04MzJhLTE4NDdmNzk5M2ZiOSJ9.kp61JLVEXpgUnuin1DpGU4HFRh2jXzcQDnz1lwxDPKFMnkW0xxNW47SiypDV6saI4TpLMkEydwDf9QURBYXQaPsTPNf3xl-vwZu2Tty_Y9geEySXJRRO0B2ip2NbLlc_3tC7JNpThWUM9RGy0skfTGZAgdBahKyiRpN6fl84AZlTCeCCJpB-TpbTG8BBIfnjdQ2zArwmSlcstR1VLWFnrMQjaelNG_Bl3NozTolN5cWGuHNzwAQ8qCrGsEHcwsQUlzgaJmG-JnX4taEUGs-IGzcX-rTGMdjDjW1nUPW_bb4edWdOY8wgaSZ_oOQeMBFKyQmaIrlSRTpiqW4DdxhZyw'
    user_id = 'SY23012003'
    consumer_key = 'rdZCG0VPAFoXk9GfSZpPNf4ZigUa'
    ip = '127.0.0.1'
    app_id = 'main'
    password = 'trade@1'
    bot = Autobot()
    bot.login(consumer_key,access_token,app_id,user_id,password)

    @app.get("/start")
    def start(stock_name,exchange="NS"):
        '''Websocket to start'''
        bot.evaluate(stock_name,exchange)

    @app.get("/rsi")
    def get_rsi(stock_name,days):
        rsi = bot.get_rsi(stock_name,days)
        return rsi
        
    # print(f"Rsi is {rsi}")
