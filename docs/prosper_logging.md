# prosper_logging
All [Prosper](https://github.com/EVEprosper) scripts use a unified logger.  `ProsperLogger` is the easy way to build/extend any logger.  Death to `print()` long live `logger`

# How to use ProsperLogger
Building a logger is easy.

```
import prosper.common.prosper_logging as p_log

LogBuilder = p_log.ProsperLogger(
    'log_name',
    'desired/log/path',
    configuration_object,
    bool:debug_mode [optional]
)

logger = LogBuilder.get_logger()
```

the `LogBuilder` can be extended with some other handlers if required.  Also, defaults can be rerun if desired.

# Built-In Handlers

## configure_default_logger

```
def configure_default_logger(
    self,
    log_freq:str,
    log_total:int,
    log_level:log_level_str,
    log_format:log_format_str,
    debug_mode:bool
):
```

* log_freq: [TimedRotatingFileHandler definition](https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler)
* log_total: how many log-periods to retain
* log_level: [desired minimum log level](https://docs.python.org/3.5/library/logging.html#levels)
* log_format: [Python log formatter string](https://docs.python.org/3.5/library/logging.html#logrecord-attributes)
* debug_mode: unused at this time

This handler is loaded by default.  It can be reset by calling `ProsperLogger().configure_default_logger(...)` again.  **THIS SHOULD BE DONE AS EARLY AS POSSIBLE** can wipe out all other attached handlers.

## configure_debug_logger

```
def configure_debug_logger(
    self,
    log_level:log_level_str,
    log_format:log_format_str,
    debug_mode:bool
):
```

* log_level: default = 'DEBUG' (print everything)
* log_format: default = `ReportingFormats.STDOUT`
* debug_mode: unused

For live debugging, report logging messages to standard out.  This can be attached by a [Plumbum.cli](http://plumbum.readthedocs.io/en/latest/cli.html) for easy toggling between debug/production logging

## configure_discord_handler

```
def configure_discord_handler(
    self,
    log_level:log_level_str,
    log_format:log_format_str,
    discord_webhook:url_str,
    discord_recipient:'<@int>'_discord_id_str,
    debug_mode:bool
):
```

* log_level: default 'ERROR'
* log_format: default `ReportingFormats.PRETTY_PRINT`
* discord_webhook: [discord webhook url](https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
* discord_recipients: `<@int>` for alerting [users](https://discordapp.com/developers/docs/resources/user#user-object)/groups (see app developer console)
* debug_mode: unused

Live alerting is a useful tool.  ProsperCommon is loaded with a REST handler for pushing logging alerts to [discord webhooks](https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks).  Any alerts above a given level will be pushed out to a discord channel along the webhook pipeline

# Logging Configuration

ProsperLogger is designed with the following priority order for finding configurations:

1. arguments in `configure_handler` calls
2. `__init__` called `configuration_object` loaded by the script that needs the logger
3. prosper.common/common_config.cfg as global defaults

## configuration_object

```
[LOGGING]
    log_level = INFO
    log_path = .
    log_freq = midnight
    log_total = 30
    discord_webhook = #SECRET
    discord_level = ERROR
    discord_alert_recipient = <@236681427817725954>
```
This section is valid in any loaded configuration object loaded by prosper.common.prosper_config `get_config()`.  Any commented/blank keys are loaded as `None` but should have error handling in place.

# ReportingFormats

[Python Log Formats](https://docs.python.org/3.5/library/logging.html#logrecord-attributes) are obnoxious to write, and leaving them in config-levels could lead to version upgrading issues later.

Instead we include some helpful baked-in formats for easy setup:

* `ReportingFormats.DEFAULT` (for file logging)

    `[2016-10-14 16:11:38,805;DEBUG;prosper_logging.py;<module>;185] prosper.common.prosper_logging TEST --DEBUG--`
    
* `ReportingFormats.PRETTY_PRINT` (for Discord logging)

    ```
    [DEBUG:prosper_logging.py--<module>:185]
    prosper.common.prosper_logging TEST --DEBUG--
    ```
    
* `ReportingFormats.STDOUT` (for std-out/console logging)

    `[DEBUG:prosper_logging.py--<module>:185] prosper.common.prosper_logging TEST --DEBUG--`
