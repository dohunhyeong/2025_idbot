class SourceService:

    def append_sources(self, answer: str, urls: list[str]) -> str:

        if not urls:
            return answer

        unique_urls = list(dict.fromkeys(urls))

        url_lines = "\n".join(f"- {url}" for url in unique_urls)

        return f"{answer}\n\n**출처**\n{url_lines}"