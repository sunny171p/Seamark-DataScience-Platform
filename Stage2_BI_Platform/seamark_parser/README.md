# seamark-ecom-parser

This is a lightweight tool I built to clean up product feeds from different supplier sources like DSers or Amazon before pushing them into a local SQL database. 

Sometimes data arrives with massive whitespace padding, missing values, or prices written as text strings instead of numbers. This utility normalizes that data.

## Local Usage Example

```python
from parser import clean_and_format_feed

messy_data = [{"sku": "  item-01 ", "price": "25.50", "stock": "10"}]
print(clean_and_format_feed(messy_data))
```