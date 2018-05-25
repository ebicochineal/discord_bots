# discord_mm95bot.py
# 必要
- python3.5  
- discord.py  
pip install discord.py  
<https://github.com/Rapptz/discord.py>  
- discord bot token  
<https://discordapp.com/developers/applications/me>  
```https://discordapp.com/oauth2/authorize?client_id=***Client ID***&scope=bot```
***Client ID***を書き換えてアクセスしbotをサーバーに呼ぶ  
# 機能
BOTにダイレクトメッセージ画像かURLを送るとtopcoderMM95で作成したプログラムを使って画像を作成してテキストチャンネルにアップロード  
画像を送る前にN=20とかでNを設定初期値1000  
  
  
discord_mm95bot.pyで画像ダウンロードimageファイル保存, lockファイル作成, circlesmix.py実行, circlesmix.png作成待ちループ  
circlesmix.py pillowで画像リサイズ, 読み取り入力データ作成, CirclesMix.exe実行結果受け取り, pillowで画像作成  
discord_mm95bot.pyで画像を設定したチャンネルに送信, lock削除  

