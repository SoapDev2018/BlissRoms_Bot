<div align="center">
  <img src="blissroms-logo.png" alt="BlissRoms Logo" width="200" height="200">
  <h1>BlissRoms Telegram Bot</h1>
</div>

Welcome to the BlissRoms Telegram Bot project! This bot is designed to provide the BlissRoms community with easy access to information about officially supported devices and download links from SourceForge for both vanilla and gapps versions of BlissRoms.

## Features

- List officially supported devices for BlissRoms.
- Provide download links for vanilla and gapps versions of BlissRoms from SourceForge.
- User-friendly interface for quick access to information.
- Auto-deletes long messages in private chats and groups (with permission) to avoid cluttering the chat.

## Getting Started

To use the BlissRoms Telegram Bot, follow these steps:

1. **Invite the Bot**: Add the bot to your Telegram group or send it a direct message. You can find the bot by searching for its username in Telegram: `@blissrom_bot`.

2. **Commands**: Use the following commands to interact with the bot:
   - `/start`: Get a welcome message and an overview of available commands.
   - `/help`: Get a help message about the available commands.
   - `/list`: View the list of officially supported devices for BlissRoms.
   - `/bliss [device]`: Get the download links for the specified device.
   - `/refresh`: Authorized users' only command. Refreshes the locally cached devices.json file.

## Examples

- To view the list of supported devices: `/list`
- To get download links for a specific device: `/bliss obiwan`

## Dependencies

- [Python 3.11](https://python.org)
- [Pyrogram](https://pyrogram.org)
- [humanfriendly](https://pypi.org/project/humanfriendly/)
- [httpx](https://www.python-httpx.org/)
- [TgCrypto](https://pypi.org/project/TgCrypto/)
- [APScheduler](https://pypi.org/project/APScheduler/)
- [PyYAML](https://pypi.org/project/PyYAML/)

## Bot Deployment

1. Install Python for your distribution
2. Run the following command to install pipenv: `pip/pip3 install pipenv`
3. Clone this repository: `git clone https://github.com/SoapDev2018/BlissRoms_Bot BlissRoms_Bot`
4. Go into the directory: `cd BlissRoms_Bot/`
5. Let pipenv install the dependencies (in a virtual environment): `pipenv install`
6. Rename `sample_config.yml` to `config.yml` and fill in the values (described below)
7. Run a pipenv shell: `pipenv shell` and then: `python bliss.py`. Alternatively: `pipenv run python bliss.py`

## YAML Values

- `api_id`: Your Telegram API_ID (from <https://my.telegram.org>)
- `api_hash`: Your Telegram API_HASH (from <https://my.telegram.org>)
- `bot_token`: Your bot's token (from <https://telegram.dog/BotFather>)
- `authorized_ids`: Authorized users, who can use the `/refresh` command
- `download_url`: BlissRoms' download URL; do not modify unless you know what you're doing!
- `user_agent`: Custom User-Agent to send to the download server
- `default_user_agent`: The default UA passed, if `user_agent` is not defined
- `group_ids`: Authorized Telegram chats, leave blank to allow all chats

## Contributing

Contributions to this project are welcome! If you'd like to contribute, follow these steps:

1. Fork the repository.
2. Create a new branch for your changes: `git checkout -b feature/new-feature`
3. Make your changes and commit them: `git commit -m "Add new feature"`
4. Push it back up to GitHub: `git push origin feature/new-feature`
5. Create a pull request from your branch to the main repository.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

If you have any questions or feedback about the BlissRoms Telegram Bot, you can reach out to the team on [Telegram](https://telegram.dog/Team_Bliss_Community) or create an issue in this repository.

Happy chatting and downloading BlissRoms!
