# NewTask
(.venv) PS C:\Users\MSI\PycharmProjects\NewTask> python main.py products.csv                  
| name             | brand   |   price |   rating |
|:-----------------|:--------|--------:|---------:|
| iphone 15 pro    | apple   |     999 |      4.9 |
| galaxy s23 ultra | samsung |    1199 |      4.8 |
| redmi note 12    | xiaomi  |     199 |      4.6 |
| poco x5 pro      | xiaomi  |     299 |      4.4 |
(.venv) PS C:\Users\MSI\PycharmProjects\NewTask> python main.py products.csv --aggregate "rating=avg"
|   avg |
|------:|
| 4.675 |
(.venv) PS C:\Users\MSI\PycharmProjects\NewTask> python main.py products.csv --where "brand=apple"
| name          | brand   |   price |   rating |
|:--------------|:--------|--------:|---------:|
| iphone 15 pro | apple   |     999 |      4.9 |
(.venv) PS C:\Users\MSI\PycharmProjects\NewTask> python main.py products.csv --where "rating>4.7"
| name             | brand   |   price |   rating |
|:-----------------|:--------|--------:|---------:|
| iphone 15 pro    | apple   |     999 |      4.9 |
| galaxy s23 ultra | samsung |    1199 |      4.8 |
