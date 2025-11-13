# 載入需要的模組
from __future__ import unicode_literals
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage,ButtonsTemplate,TemplateSendMessage,PostbackAction,MessageAction,URIAction,ConfirmTemplate,PostbackEvent,MessageTemplateAction
import requests
import json
import redis
import re




#连接redis库储存数据
pool = redis.ConnectionPool(
    host=os.getenv('ALY_IP'),
    port=6379,
    password=os.getenv('ALY_PWD'),
    db=0,
    max_connections=20,  # 最大连接数
    decode_responses=True
)

r = redis.Redis(connection_pool=pool)




app = Flask(__name__)

user = os.getenv('QH_USER')
psd = os.getenv('QH_PWD')
user_states = {}




# 登录函数
def login(user,psd):
    url = "https://api.tongzhou666.com/replaceCharge/token"
    body = "erBanNo="+user+"&password="+psd
    heard = {
        "Host": "api.tongzhou666.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        "Referer": "https://api.tongzhou666.com/front/charge_withdraw/login.html",
        "Origin": "https://api.tongzhou666.com"
        }
    response_str = requests.post(url=url,data=body,headers=heard)
    response_data = json.loads(response_str.text)
    # print(response_data)
    token_value = response_data['data']['token']
    voucherNum = response_data['data']['voucherNum']
    r.set('user_token', token_value)
    print("token的值为:" + token_value)
    print(voucherNum)
    return(token_value)

# 查询金额函数
def money(user,psd):
    url = "https://api.tongzhou666.com/replaceCharge/token"
    body = "erBanNo="+user+"&password="+psd
    heard = {
        "Host": "api.tongzhou666.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        "Referer": "https://api.tongzhou666.com/front/charge_withdraw/login.html",
        "Origin": "https://api.tongzhou666.com"
        }
    response_str = requests.post(url=url,data=body,headers=heard)
    response_data = json.loads(response_str.text)
    voucherNum = response_data['data']['voucherNum']
    return(voucherNum)

#充值函数
def Recharge(num,sentid):
    url = "https://api.tongzhou666.com/replaceCharge/giveVoucher"
    body = "erBanNo="+sentid+"&giveNum="+num+"&pwd=&token="+r.get('user_token')+"&uid=5191746"
    heard = {
        "Host": "api.tongzhou666.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        "Referer": "https://api.tongzhou666.com/front/charge_withdraw/login.html",
        "Origin": "https://api.tongzhou666.com"
        }
    response_str = requests.post(url=url,data=body,headers=heard)
    response_data = json.loads(response_str.text)
    return(response_str.text)
    
#查询客户信息函数
def lookforward(userid):
    token = r.get('user_token')
    url = "https://api.tongzhou666.com/replaceCharge/checkUser?erBanNo="+userid+"&token="+token+"&uid=5191746"
    heard = {
        "Host": "api.tongzhou666.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        "Referer": "https://api.tongzhou666.com/front/charge_withdraw/login.html",
        "Origin": "https://api.tongzhou666.com"
        }
    response_str = requests.get(url=url,headers=heard)
    response_data = json.loads(response_str.text)
    user_name_one = response_data.get('data')
    if user_name_one is None:
        user_name = "用户id不正确，请检查！"
    else:
        user_name = user_name_one['nick']





    # user_name = response_data['data']['nick']
   
    

    print("查询到的用户昵称为："+user_name)
    return(user_name)






# LINE 聊天機器人的基本資料
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
# 收到充值消息单线程充值
@line_handler.add(MessageEvent, message=TextMessage)
def echo(event):
    
    msg = event.message.text
    user_id = event.source.user_id 
    # if user_states.get(user_id) == 'awaiting_confirmation':
    #     return
    if "ID"and"名字"and"金币"and"金额"and"币种" in msg:
        
        if r.exists('发单人员'):
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"已有他人发单中，请稍后"))
            return
        else:
            r.setex('发单人员',60,user_id)

        
        
        
        # cheak1 = r.exists('充值ID')
        # cheak2 = r.exists('充值金币')
        cheak3 = int(r.get(user_id))
        # if cheak1:
        #     line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=f"已有订单正在执行，请稍后再试"))
        #     return

        # if cheak2:
        #     line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=f"已有订单正在执行，请稍后再试"))
        #     return

        if cheak3 < 0:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"余额不足，请联系管理员充值"))
            r.delete('发单人员')
            return

        user_states[user_id] = 'awaiting_confirmation'
        data = {}
        for line in msg.strip().split('\n'):
         key, value = line.split(':', 1)
         data[key] = value

        id_value = data['ID']
        name_value = data['名字']
        coin_value = data['金币']
        amount_value = data['金额']
        currency_value = data['币种']
     
        cleaned_id = id_value.replace('\n', '').replace(' ', '')
        cleaned_coin = coin_value.replace('\n', '').replace(' ', '')
        
        end_id = cleaned_id
        end_coin = cleaned_coin

        if "台" in currency_value:
            num1 = int(cleaned_coin)
            num2 = int(amount_value)
            num3 = num1 / num2
            if num3 != 21 :
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"金币与金额不符合，请计算后重发"))
                if r.getex('发单人员') == user_id :
                    r.delete('发单人员')
                return

        if "马" in currency_value:
            num1 = int(cleaned_coin)
            num2 = int(amount_value)
            num3 = num1 / num2
            if num3 != 150 :
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"金币与金额不符合，请计算后重发"))
                if r.getex('发单人员') == user_id :
                    r.delete('发单人员')
                return

        if "新" in currency_value:
            num1 = int(cleaned_coin)
            num2 = int(amount_value)
            num3 = num1 / num2
            if num3 != 450 :
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"金币与金额不符合，请计算后重发"))
                if r.getex('发单人员') == user_id :
                    r.delete('发单人员')
                return

        if "馬" in currency_value:
            num1 = int(cleaned_coin)
            num2 = int(amount_value)
            num3 = num1 / num2
            if num3 != 150 :
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"金币与金额不符合，请计算后重发"))
                if r.getex('发单人员') == user_id :
                    r.delete('发单人员')
                return




        r.set('充值ID', end_id)
        r.set('充值金币', end_coin)
        print(r.get('充值ID'))
        print(r.get('充值金币'))

        login(user,psd)
        
        name = lookforward(end_id)
        if name == "用户id不正确，请检查！" :
            if r.getex('发单人员') == user_id :
                    r.delete('发单人员')
                    r.delete('充值ID')
                    r.delete('充值金币')  
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text= "用户id不正确，请检查！"))
            return

        
        
        confirm_template_message = TemplateSendMessage(
            alt_text="检查订单",
            template=ConfirmTemplate(
                text="请确认以下信息：\n\nID:"+end_id+"\n名字:"+name+"\n金币:"+end_coin+"\n金额:"+amount_value+"\n币种:"+currency_value,
                actions=[
                    PostbackAction(
                        label='确认',
                        display_text='订单已确认',
                        data='action=confirm&item=123'),
                    PostbackAction(
                        label='取消',
                        display_text='订单取消，有需要请重新发单',
                        data='action=cancel&item=321')
                ]
            )
        )
        
        message = confirm_template_message
        line_bot_api.reply_message(event.reply_token, message)
        
    
    elif '绑定' in msg:
        if r.exists(user_id):
            message = TextSendMessage(text="您已有账户，目前余额为：" + r.get(user_id))
            line_bot_api.reply_message(event.reply_token, message)
        else:
            r.set(user_id,"0")
            account = r.get(user_id)
            message = TextSendMessage(text="绑定成功，userid为：" + user_id +",余额为：" + r.get(user_id))
            line_bot_api.reply_message(event.reply_token, message)

        
        
    
    elif '我的token' in msg:
        u_token = event.reply_token
        message = TextSendMessage(text="您的token:"+u_token)
        line_bot_api.reply_message(event.reply_token, message)
    
    elif '增加额度' in msg:
        text = msg
        parts = text.split("增加额度")
        if len(parts) == 2:
             hash_value = parts[0]
             number = parts[1]
             print("哈希值:", hash_value)  # Uee072eed60877baa2b0b4d5b612edec1
             print("数字:", number)  # 100
        balance = int(r.get(hash_value))
        addnum = int(number)
        newbalance = str(balance + addnum)
        end_balance = r.set(hash_value, newbalance)
        re_text = hash_value + "账户额度增加成功，目前该账户余额为：" + newbalance
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=re_text))
    elif '我的额度' in msg:
        if r.exists(user_id):
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text= user_id + "账户剩余额度为：" + r.get(user_id)))
        else:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="未创建账户，请先绑定"))



        



        
    else:
        message = TextMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)
    
@line_handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    user_id = event.source.user_id 
    # 解析数据
    from urllib.parse import parse_qs
    data_dict = parse_qs(data)

    if data_dict.get('action', [''])[0] == 'cancel':

        if r.get('发单人员') == user_id:
            r.delete('充值ID')
            r.delete('充值金币')
            r.delete('发单人员')
            return
        if r.exists('发单人员'):
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"有其他成员正在充值，请稍后"))
        else:
            r.delete('充值ID')
            r.delete('充值金币')
            r.delete('发单人员')
     

        
        


    if data_dict.get('action', [''])[0] == 'confirm':
        item_id = data_dict.get('item', [''])[0]
        
        # 执行你的指定函数
        

                










        num = r.get('充值金币')
        sentid = r.get('充值ID')
        if r.exists('发单人员'):
            result = Recharge(num,sentid)
            result1 = json.loads(result)
            result2 = result1['message']
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"未获取到订单，请发单"))
            return

        
        
        if "success" in result2 :  
            
            balance = int(r.get(user_id))
            addnum = int(r.get('充值金币'))
            newbalance = str(balance - addnum)
            r.set(user_id, newbalance)
   
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"充值成功，您当前剩余额度为：" + r.get(user_id)))
            r.delete('充值金币')
            r.delete('充值ID')
            r.delete('发单人员')
        else:
            r.delete('发单人员')
            r.delete('充值ID')
            r.delete('充值金币')
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"充值失败，请检查订单或联系管理员"))

            

        






if __name__ == "__main__":
    app.run()







