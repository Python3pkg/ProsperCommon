# prosper_config
Parsing global/local configs can be obnoxious.  We provide a way to use/override configs.  Especially for libraries, a way to control globals or override them.

All [Prosper](https://github.com/EVEprosper) use the `ProsperConfig` parser.  Powered by py3's `configparser`.

# How to use ProsperConfig

```python
import prosper.common.prosper_config as p_config

ConfigObj = ProsperConfig(
    'path/to/config.cfg'
    local_filepath_override='path/to/custom_config.cfg' #optional
)

option_value = ConfigObj.get_option('SECTION_NAME', 'KEY_NAME', override_value, default_value)
```

This should give the following priority for `option_value`

1. if override_value != default_value: override value.  A value given at arg time
2. whatever the `local_config['SECTION_NAME']['KEY_NAME']` would yield.  Untracked config file
3. whatever the `global_config['SECTION_NAME']['KEY_NAME']` would yield.  Git tracked config file
4. `default_value` as a final result to avoid returning `None` where it wouldn't be supported

