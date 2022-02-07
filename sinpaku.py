#本プログラムは，fitbitから心拍数を取得し，HFを計算します．
# 「####」で囲まれている部分は，各PCで変更する必要があります


import fitbit
from ast import literal_eval
import pandas as pd
import numpy as np
from pandas._libs.tslibs import timestamps
import pyhrv.frequency_domain as fd


"""
下記サイトを参考に，fitbitapi に登録
キーの取得及び，TOKEN_FILEの作成をおこなう
https://sabopy.com/py/fitbit-1/

"""

#######################################
CLIENT_ID     = "237Y4F" 
CLIENT_SECRET = "19c899d2e2f97d75bcede4a9261e1155" 
TOKEN_FILE    = "token.txt"
#######################################

#認証
tokens = open(TOKEN_FILE).read()
token_dict = literal_eval(tokens)
access_token = token_dict['access_token']
refresh_token = token_dict['refresh_token']

def updateToken(token):
    f = open(TOKEN_FILE, 'w')
    f.write(str(token))
    f.close()
    return
 
client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET,
    access_token = access_token, refresh_token = refresh_token, refresh_cb = updateToken)


#取得したい日を設定
DATE = "2022-01-20"

# 心拍数を取得
data_sec = client.intraday_time_series('activities/heart', DATE, detail_level='1sec')
heart_sec = data_sec["activities-heart-intraday"]["dataset"]
heart_rat = pd.DataFrame.from_dict(heart_sec)

#時間データの整理
date_ser =pd.Series(np.zeros(len(heart_rat)))
date_ser[:]= DATE
times = date_ser.str.cat(heart_rat['time'],sep=' ')
heart_rat['time'][0:len(heart_rat)]= times

#print(heart_rat)
#下記コードの参考サイトURL
#https://zenn.dev/techdoctor_dev/articles/2cce9a6326401f
#HFの計算準備
heartrate_df = heart_rat.assign(
    mrri=lambda df: 60 / df['value'] * 1000
)

fhf_res = heartrate_df.assign(
        timestamp=lambda df: pd.to_datetime(df['time'])
    )

fhf_res = fhf_res.set_index('timestamp')

#不要なデータ列の削除
del fhf_res['value']
del fhf_res['time']

#新しく得られるHFデータの格納場所
HF=[]
time=[]

#HF計算部分
#2022/01/20の17時13分から52分の40分間，一分毎にHFの計算を行う．
for i in [13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52]:
    try:
        #HF計算の範囲の設定　13分から14分の一分間のHFを算出する．その後52分まで繰り返す
        a='2022-01-20 17:'+str(i)+':00'
        b='2022-01-20 17:'+str(i+1)+':00' 

        #配列の作成
        HF.append(fhf_res.loc[a:b].apply(lambda x:fd.ar_psd(nni=x,mode='dev')[0]['ar_norm'][1])['mrri'])
        time.append(a)     

    except AssertionError:
        #一分間のデータ数が足りない場合にでるエラー処理．前後15秒も含めて心拍数を取得しHFを計算
        a='2022-01-20 17:'+str(i-1)+':45'
        b='2022-01-20 17:'+str(i+1)+':15' 
        c='2022-01-20 17:'+str(i)+':00'

        #配列の作成          
        HF.append(fhf_res.loc[a:b].apply(lambda x:fd.ar_psd(nni=x,mode='dev')[0]['ar_norm'][1])['mrri'])
        time.append(c)

#配列を元にデータフレーム作成
dic_arr={'time':time,'HF':HF}
result=pd.DataFrame(dic_arr)


#結果の出力
result.T.to_csv('result.csv')
print(result)



