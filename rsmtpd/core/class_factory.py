from typing import Type, Union, cast

from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.core.logger_factory import LoggerFactory


class ClassFactory:
    """
    The ClassFactory is instantiated by the worker and loads the command handler instances along with other necessary
    classes we may need.
    """

    def __init__(self, logger_factory: LoggerFactory, config_loader: ConfigLoader):
        self.__logger_factory = logger_factory
        self.__config_loader = config_loader

        self.__logger = logger_factory.get_module_logger(self)
        self.__instances = {}

        self.__logger.debug("ModuleFactory ready")

    def get_instance(self, module_name: str, class_name: str, enforce_type: Type) -> Union[Type, None]:
        instance_name = f"{module_name}::{class_name}"

        if instance_name in self.__instances:
            return self.__instances[instance_name]

        try:
            module = __import__(module_name)
            for sub in module_name.split(".")[1:]:
                module = getattr(module, sub)
            class_ref = getattr(module, class_name)

            if not issubclass(class_ref, enforce_type):
                self.__logger.error(f"Class {class_name} in module {module_name} does not inherit from"
                                    f" {enforce_type.__name__}; class will not be used")
                return None

            self.__logger.debug(f"Instantiating class {class_name} in module {module_name}")
            class_ref = cast(enforce_type, class_ref)
            instance = class_ref(self.__logger_factory.get_child_logger(class_name), self.__config_loader, "")
            self.__logger.debug(f"Class {class_name} in module {module_name} successfully instantiated")
            self.__instances[instance_name] = instance
            return instance
        except Exception as e:
            self.__logger.error(f"Unable to load class: {module_name}.{class_name} does not exist {e}")
            return None
