# Wreaclast Currency Tracker (PoE2)

A fast, lightweight Python utility designed to calculate, value, and track your true net worth in Path of Exile 2. By scanning your stash and fetching live economy rates directly from **poe.ninja**, it eliminates manual conversion math and provides instantaneous visibility into your farming efficiency.

---

## ✨ Features

*   **Dual-Focus Valuation:** Displays your stash breakdown simultaneously in **Chaos View** and **Divine View**, letting you immediately analyze bulk assets vs. high-liquid wealth.
*   **Live Market Integration:** Pulls real-time market data directly from the poe.ninja API (`Runes of Aldur` league).
*   **Normalized Value Anchors:** Automatically corrects API market variances, ensuring 1 Chaos = 1c and 1 Divine = 1d baselines are rigidly enforced.
*   **Comprehensive Key Mapping:** Custom translation layer maps obscure internal API item IDs to clear, recognizable in-game item names.

---

## 📊 Sample Output

```text
[*] Fetching live PoE2 economy rates from poe.ninja...

======================================================================
                STASH CURRENCY BREAKDOWN (CHAOS VIEW)                 
======================================================================
Item ID                          | Qty   | Unit Price   | Total Chaos 
----------------------------------------------------------------------
divine-orb                       | 116   |      7.1100c |      824.8c
fracturing-orb                   | 1     |     77.7834c |       77.8c
perfect-chaos-orb                | 1     |     40.1715c |       40.2c
perfect-exalted-orb              | 1     |     20.7612c |       20.8c
perfect-orb-of-augmentation      | 27    |      0.6706c |       18.1c
chaos-orb                        | 13    |      1.0000c |       13.0c
exalted-orb                      | 581   |      0.0166c |        9.6c
regal-orb                        | 651   |      0.0136c |        8.9c
vaal-orb                         | 130   |      0.0595c |        7.7c
greater-chaos-orb                | 2     |      3.0417c |        6.1c
----------------------------------------------------------------------
💰 Total Net Worth: 1,043.3 c
======================================================================

======================================================================
                STASH CURRENCY BREAKDOWN (DIVINE VIEW)                
======================================================================
Item ID                          | Qty   | Unit Price   | Total Divine
----------------------------------------------------------------------
divine-orb                       | 116   |    1.00000d |    116.000d
fracturing-orb                   | 1     |   10.94000d |     10.940d
perfect-chaos-orb                | 1     |    5.65000d |      5.650d
perfect-exalted-orb              | 1     |    2.92000d |      2.920d
perfect-orb-of-augmentation      | 27    |    0.09432d |      2.547d
chaos-orb                        | 13    |    0.14065d |      1.828d
exalted-orb                      | 581   |    0.00233d |      1.355d
----------------------------------------------------------------------
✨ Total Net Worth: 146.74 div  (1 div = 7.11c)
======================================================================
```

## 🚀 Getting Started

### Prerequisites
* **Python 3.10+**
* Dependencies listed in `requirements.txt`

### Installation
1. **Clone the repository and navigate to the project root:**
  ```bash
   git clone [https://github.com/yourusername/wreaclast-currency.git](https://github.com/yourusername/wreaclast-currency.git)
   cd wreaclast-currency/source
  ```

2. **Install the required Python packages:**
  ```bash
   pip install -r requirements.txt
  ```
   
## Running the App
Ensure your stash grid scanner has run and produced a valid stash_report.json file in your source directory. Then execute the calculation engine:
   ```bash
   python calculate_wealth.py
  ```