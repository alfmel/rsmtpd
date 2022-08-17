# Response Variables

When crafting a response you may specify one of the following variables (including `<>`):

| Variable                   | Value                                                                                                                   |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `<server_name>`            | The domain of the server set initially in config/rsmtpd.yaml::sever_name and later by TLS based on the certificate name |
| `<version>`                | The RSMTPD version (defined in core/worker.py)                                                                          |
| `<client.ip>`              | The client's IP address                                                                                                 |
| `<client.port>`            | The client's remote port                                                                                                |
| `<client.advertised_name>` | The client's name as given during the HELO/EHLO command                                                                 |

Any other value (such as `<does_not_exist>`) will remain unchanged.
