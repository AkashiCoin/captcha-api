# captcha-api  
Multi captcha solver API, thanks for [turnaround](https://github.com/Body-Alhoha/turnaround). Made using Python & fastapi

## Example  
Python code example [here](https://github.com/AkashiCoin/captcha-api/blob/main/test.py)

## Installing  
First, install the requirements:  
```bash
pip install -r requirements.txt
```
If it's your first time running playwright or you're using a virtual environment, you'll need to install the playwright browser:  
```bash
python -m playwright install
```
Then, run the server:
```bash
python main.py run
```
The server will be running on port 8001 by default, you can change it in config.py.
Also you can visit `http://127.0.0.1:8001/doc` see the doc

---

For openai har file, you can run:  
```bash
python main.py har
```
Then, har files will outpuy to `harPool` dir


## Contributing  
Contributions are welcome, feel free to open a pull request or an issue

## Credits  
[turnaround](https://github.com/Body-Alhoha/turnaround/) for the original solver