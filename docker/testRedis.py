import redis
from datetime import datetime

# datetime object containing current date and time
now = datetime.now()
 
#print("now =", now)

# dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
#print("date and time =", dt_string)
#r = redis.Redis(host='redis',port=6379)
#r = redis.Redis(host='matlab_redis_1',port=6379)
### r = redis.Redis(host='DTredis',port=6380) # se lo lancio dal container
r = redis.Redis(host='localhost',port=6380)  # se lo lancio dall'host
r.set('foo', 'Redis Funziona!')
r.set('testOggi', dt_string)
valueMessaggio=r.get('foo').decode('utf-8')
valueData=r.get('testOggi').decode('utf-8')
print("Oggi ", valueData)
print(valueMessaggio)

