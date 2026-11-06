# EditedAPI

Repository containing documentation and code samples for specific API use cases and functions to help developers quickly learn how to use our APIs.

## Installation

You can install the `editedapi` module in the following way:

### Install Directly from GitHub (latest version)

To install the `editedapi` module directly from GitHub, run this command:

```
pip install git+https://github.com/EDITD/edited-api-use-case-guides.git
```

### Clone the Repository
The above command will build and install the `editedapi` module for your use, but it does not clone the repository. In order to run any of the pre-built use cases, you should clone the repository locally:

```
git clone https://github.com/EDITD/edited-api-use-case-guides.git
```

### Configuration

These use case guides require a configuration file named `config.ini` to be placed in the root directory of the project. Copy the template `config.ini.example` to `config.ini` and edit it to use your provided API Key as well as any other optional configurations which might be used by the sample use cases guides.

```
cp config.ini.example config.ini      # Windows: copy config.ini.example config.ini
```

`config.ini` is gitignored so your key is never committed; only the placeholder template `config.ini.example` is tracked. Never put a real key in `config.ini.example`.

Template contents:

```
#config.ini

[api]
; Required Configuration Parameters
log_level = INFO
api_key = <YOUR_API_KEY>

; Optional Configuration Parameters
filterset_id = <YOUR_FILTER_SET_ID>
```
