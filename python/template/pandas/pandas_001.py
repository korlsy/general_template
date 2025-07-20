import pandas as pd

data = {'이름': ['홍길동', '이순신', '강감찬'],
        '나이': [50, 40, 30],
        '직책': ['부장', '차장', '과장']}

df = pd.DataFrame(data)

print(df)

