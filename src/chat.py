from pathlib import Path
from dotenv import load_dotenv
from dougbot_model import Dougbot

ROOT=Path(__file__).resolve().parents[1]

def main():
    load_dotenv(ROOT/".env")
    bot=Dougbot()
    print(f"Dougbot local chat. adapter={'on' if bot.using_adapter else 'off'}; device={bot.device}. Ctrl+C to quit. 🌶️")
    while True:
        try: q=input("you> ").strip()
        except (EOFError,KeyboardInterrupt): break
        if not q: continue
        print("dougbot>",bot.reply(q))
if __name__=="__main__": main()
