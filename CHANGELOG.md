# CHANGELOG

<!-- version list -->

## v0.0.2 (2026-09-22)


## v0.0.1 (2026-09-22)

### Bug Fixes

- **agent**: Scope cache by enabled capabilities
  ([`6cf664a`](https://github.com/tropical-algae/snapbot/commit/6cf664a4906143ced71607da32ecfad30874a7b8))

- **plugin**: Remove /test command
  ([`be53ed9`](https://github.com/tropical-algae/snapbot/commit/be53ed962d04fa45cffa6628eebe8b63de229d55))

- **typing**: Resolve mypy and static analysis issues
  ([`6131690`](https://github.com/tropical-algae/snapbot/commit/61316901e619057bbf537ea8c29e50b34ab879d4))

### Chores

- **config**: Add initial project tools
  ([`4d92ca2`](https://github.com/tropical-algae/snapbot/commit/4d92ca28b65c8018f3ade7a5fc676420640d3081))

- **dep**: Update ruff rule and add new dependence
  ([`1d52069`](https://github.com/tropical-algae/snapbot/commit/1d5206981782426b37e7539d24e9d8b6e97f7b6e))

- **deps**: Add filelock for thread-safe file IO
  ([`eff918a`](https://github.com/tropical-algae/snapbot/commit/eff918aa21af2a9ec7a57e8ef8b4f1a15009df95))

- **deps**: Update tavily dependency lib
  ([`db9d771`](https://github.com/tropical-algae/snapbot/commit/db9d7715a0fe2c7498a4cb5c9f45e3e8fb940a7c))

### Continuous Integration

- Add quality gate for pushes and pull requests
  ([`e2c852a`](https://github.com/tropical-algae/snapbot/commit/e2c852af15d1e5db6c762c4593c1a6e333a1ca64))

- **release**: Automate semantic release and Docker publishing
  ([`01d1d82`](https://github.com/tropical-algae/snapbot/commit/01d1d82cbb1ddb7c07445a523ac5daa34fa4aa11))

### Features

- **agent**: Add streaming inference event handling
  ([`446220b`](https://github.com/tropical-algae/snapbot/commit/446220bfee77c7d1892eaafb2bf69c02bbe38ee3))

- **agent**: Refactor architecture and introduce agent memory middleware
  ([`8d78a8e`](https://github.com/tropical-algae/snapbot/commit/8d78a8e4784b4bba4a575462602850736c9fa816))

- **agent**: Support incremental token streaming
  ([`4977fcb`](https://github.com/tropical-algae/snapbot/commit/4977fcbd1bb6d88bde5bc0af932c54ec76d92e63))

- **agent**: Support per-agent models and tool filtering
  ([`212db51`](https://github.com/tropical-algae/snapbot/commit/212db513ee5d31e81c486badf34b000c4442a9d3))

- **bot**: Add qq bot plugin
  ([`b1681d7`](https://github.com/tropical-algae/snapbot/commit/b1681d76b75c4c176552ff698caa471764252506))

- **bot**: Update SnapBotPlugin
  ([`83f50f0`](https://github.com/tropical-algae/snapbot/commit/83f50f04216e297940f5c86cda7122b5dd998645))

- **core**: Scaffold agent architecture
  ([`8c5eb45`](https://github.com/tropical-algae/snapbot/commit/8c5eb451c1c12e10a0682e7de94623fd5f2722b1))

- **deploy**: Add Docker and Compose deployment
  ([`0b365b9`](https://github.com/tropical-algae/snapbot/commit/0b365b90b817926b39dc26b819dac66df825d4d8))

- **file**: Optimize file system manage function
  ([`a0355ea`](https://github.com/tropical-algae/snapbot/commit/a0355ea771c967a1f911528dd30c4af6a858ff6d))

- **log**: Save event stream to local in debug mode
  ([`6ba48f8`](https://github.com/tropical-algae/snapbot/commit/6ba48f87cc12882a13d9af6af73c7e63a611211c))

- **logger**: More logger configuration support
  ([`988f771`](https://github.com/tropical-algae/snapbot/commit/988f771063965a8adb4704d0bd3989f720a803e1))

- **mcp**: Integrate external tool servers
  ([`85e4359`](https://github.com/tropical-algae/snapbot/commit/85e4359584b9afc92bbd8cc55a9dbf6f17592eab))

- **memory**: Optimize memory subagent and tools
  ([`bad4e15`](https://github.com/tropical-algae/snapbot/commit/bad4e157fddb59bf7058ccbf18c5b67843069670))

- **middleware**: Add FileMemoryMiddleware for agent
  ([`9ccb383`](https://github.com/tropical-algae/snapbot/commit/9ccb3832dd29f20dbe04207dab5eb485136c9c1c))

- **prompt**: Add prompt for memory and agents
  ([`e44185c`](https://github.com/tropical-algae/snapbot/commit/e44185cf85f3d910d6223b5fbe934b9b649ba5f8))

- **prompt**: Add prompts for the comic downloader agent
  ([`7c3c152`](https://github.com/tropical-algae/snapbot/commit/7c3c1528658a32142881225fb7deee8be2ef80dc))

- **prompt**: Optimize system prompt and subagent description
  ([`03ce133`](https://github.com/tropical-algae/snapbot/commit/03ce1336d001cf1708f68712afe476987172af80))

- **prompt**: Refine agent descriptions and prompts, and add prompts for the group operator agent
  ([`2e6dbd6`](https://github.com/tropical-algae/snapbot/commit/2e6dbd646228633dc61fcd9d3f6a6ca01e1c742a))

- **tool**: Add 8 tools for group_operator agent
  ([`0fec85f`](https://github.com/tropical-algae/snapbot/commit/0fec85ffa34360ec11389e05180cd71e98f4f137))

- **tool**: Add four tools for identity and preference memory
  ([`ac1a7ea`](https://github.com/tropical-algae/snapbot/commit/ac1a7ea9eb6580e2f5a67b339850ff8fa7eb299b))

- **tool**: Add jm downloader tools
  ([`81bd5b6`](https://github.com/tropical-algae/snapbot/commit/81bd5b664f4bb9f3706d3d5ab8ccfc39f1b8017c))

- **tool**: Add volcano tts tool
  ([`d86fb54`](https://github.com/tropical-algae/snapbot/commit/d86fb54f6c21fc1845f85e9354cf5c0e603e5a3e))

- **tool**: Optimize tool configuration and tool decorator
  ([`4e4f133`](https://github.com/tropical-algae/snapbot/commit/4e4f133f84a3d091dd3da6ed3c974ec853474a64))

- **tool**: Remove action_message in tool meta
  ([`50b2445`](https://github.com/tropical-algae/snapbot/commit/50b24456b49681b2c4d47218afa71e559a2d68dd))

- **tool**: Support artifact output and retrieval
  ([`9ee0459`](https://github.com/tropical-algae/snapbot/commit/9ee0459e49c96f709b34492bfffa83a59b221e6e))

### Refactoring

- **agent**: Optimize agent name
  ([`98a4db4`](https://github.com/tropical-algae/snapbot/commit/98a4db4129420d5b21b6899bed8e6c904c86941c))

- **agent**: Optimize the agent structure
  ([`a842cf2`](https://github.com/tropical-algae/snapbot/commit/a842cf23b0c6feff730636c921265a0467a06cfa))

- **agent**: Replace custom event protocol with AG-UI
  ([`3fe2399`](https://github.com/tropical-algae/snapbot/commit/3fe239944bb42d8b2bd756dd6aef14576acfb36c))

- **agent**: Split agent enum into RootAgentName and SubAgentName
  ([`5405552`](https://github.com/tropical-algae/snapbot/commit/540555292cc86d99eeace265067d4d8618342d0c))

- **bot**: Rewrite ncatbot plugin
  ([`dbc0b46`](https://github.com/tropical-algae/snapbot/commit/dbc0b4615ced5d24f633c76f2c90d5546213627c))

- **config**: Migrate flat configuration to hierarchical YAML structure
  ([`b724c16`](https://github.com/tropical-algae/snapbot/commit/b724c16bfc0a93edda2e57beef813fa09594d703))

- **prompt**: Replace manual path config with dynamic rule-based resolution
  ([`95c935a`](https://github.com/tropical-algae/snapbot/commit/95c935a8f459b3c10e62021f858feba1134dc74f))

- **tools**: Localize descriptions and standardize input schemas
  ([`90a6d55`](https://github.com/tropical-algae/snapbot/commit/90a6d55a1560075a2fb1adcf3a352f42a973d6bb))
