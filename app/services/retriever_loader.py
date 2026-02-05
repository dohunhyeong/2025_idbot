import importlib


class RetrieverLoader:

    BASE_PACKAGE = "app.services.retrievers"

    def load(self, retriever_names):

        retriever_instances = []

        for name in retriever_names:

            try:
                module = importlib.import_module(
                    f"{self.BASE_PACKAGE}.{name}"
                )

                class_name = self._to_class_name(name)

                retriever_class = getattr(module, class_name)

                retriever_instances.append(retriever_class())

            except Exception as e:
                print(f"[RetrieverLoader] load fail: {name} → {e}")

        return retriever_instances

    def _to_class_name(self, name):

        parts = name.split("_")
        return "".join(p.capitalize() for p in parts) + "Retriever"