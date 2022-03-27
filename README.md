# osu! Collection Factory

## Dependencies

- Python 3: [Download link](https://www.python.org/downloads/)
- `dotenv`, `requests` pypl modules: To install them enter the following commands in cmd or a terminal <sup><a href="#note1">1</a></sup>:

    ```bash
    pip install requests
    ```

    ```bash
    pip install python-dotenv
    ```

- If contributing - `pytest` is required:

    ```bash
    pip install pytest
    ```

**Note: Some collection names or file names may cause issues. If you get errors try using a basic name such as `collection.db` or `collection.html` instead.**

## How to save your osu!api ID and secret key

1. Create file named `.env`
2. In `.env` write the following:

    ```txt
    ID = Your user ID
    SECRET = The client's secret key
    ```

(*This is optional, the program will prompt the user if the ID or secret isn't found.*)

## App navigation

To start, navigate to the collection factory directory and run the following <sup><a href="#note1">1</a></sup>:

```bash
python3.10 -m main
```

You will then be presented with a menu:
| Option | Function | Description | Notes |
|--------|----------|-------------|-------|
|   1    | Create collection from osu!collector collection | Create a collection from a osu!collector collection ID | <sup><a href="#note2">2</a></sup>, <sup><a href="#note3">3</a></sup>|
|   2    | Create collection from file | Create a collection from map or set IDs in a specific file | |
|   3    | Settings | Change specfic program settings | <sup><a href="#note4">4</a></sup> |

Follow the prompts and enjoy :)

### Notes

<p id="note1">1. Commands may differ from platform to platform.</p>
<p id="note2">2. If you want to filter maps by either the min or max of the chosen filter, enter 0 (or press `enter`) for the other option (ei: min=60, max=0). For 
              a specific range, note that the range is **exclusive**. </p>
<p id="note3">3. When downloading with a star rating or bpm filter, osu!Collector pages (one page = 100 maps) are
              grabbed at 1 per second. Otherwise, all maps are grabbed instantly and all at once. </p>
<p id="note4">4. Program settings may be change manually by modifting `settings.json`, however it is recommended to use the program to change them as there are basic
              sanity checks in place. </p>

<br></br>

###### Huge thanks to [The1Divider](https://github.com/The1Divider) for his contributions to the project
