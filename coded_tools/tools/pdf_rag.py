# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# END COPYRIGHT

"""Tool module for doing RAG from a pdf file"""

import logging
import os
from typing import Any
from typing import Dict
from typing import List

import tempfile
from pathlib import Path
from urllib.parse import urlparse
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.tools.base_rag import BaseRag
from coded_tools.tools.base_rag import PostgresConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PdfRag(CodedTool, BaseRag):
    """
    CodedTool implementation which provides a way to do RAG on pdf files
    """

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
        """
        Load a PDF from URL, build a vector store, and run a query against it.

        :param args: Dictionary containing:
          "query": search string
          "urls": list of pdf files
          "save_vector_store": save to JSON file if True
          "vector_store_path": relative path to this file

        :param sly_data: A dictionary whose keys are defined by the agent
            hierarchy, but whose values are meant to be kept out of the
            chat stream.

            This dictionary is largely to be treated as read-only.
            It is possible to add key/value pairs to this dict that do not
            yet exist as a bulletin board, as long as the responsibility
            for which coded_tool publishes new entries is well understood
            by the agent chain implementation and the coded_tool implementation
            adding the data is not invoke()-ed more than once.

            Keys expected for this implementation are:
                None
        :return: Text result from querying the built vector store,
            or error message
        """
        # Extract arguments from the input dictionary
        query: str = args.get("query", "")
        urls: List[str] = args.get("urls", [])

        # Validate presence of required inputs
        if not query:
            return "❌ Missing required input: 'query'."
        # Allow empty urls if loading from a pre-built vector store
        vector_store_path = args.get("vector_store_path", "")
        if not urls and not vector_store_path:
            return "❌ Missing required input: 'urls'."

        # Vector store type
        vector_store_type: str = args.get("vector_store_type", "in_memory")
        if isinstance(vector_store_type, str):
            vector_store_type = vector_store_type.strip().lower().replace("-", "_")
            if vector_store_type in ("inmemory", "in_memory", "memory"):
                vector_store_type = "in_memory"
        args["vector_store_type"] = vector_store_type

        # Save the generated vector store as a JSON file if True
        self.save_vector_store = args.get("save_vector_store", False)

        # Configure the vector store path
        raw_path = args.get("vector_store_path")
        if raw_path:
            data_dir = Path(os.getenv("NEURO_SAN_DATA_DIR", str(Path.cwd() / ".neuro_san")))
            data_dir.mkdir(parents=True, exist_ok=True)
            p = Path(raw_path)
            vector_store_path = p if p.is_absolute() else (data_dir / p)
            self.configure_vector_store_path(str(vector_store_path))
        else:
            self.configure_vector_store_path(None)

        # For PostgreSQL vector store
        if vector_store_type == "postgres":
            postgres_config = PostgresConfig(
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
                database=os.getenv("POSTGRES_DB"),
                table_name=args.get("table_name"),
            )
        else:
            postgres_config = None

        # Prepare the vector store
        vector_store: VectorStore = await self.generate_vector_store(
            loader_args={"urls": urls}, postgres_config=postgres_config, vector_store_type=vector_store_type
        )

        # Run the query against the vector store
        return await self.query_vectorstore(vector_store, query)

    async def load_documents(self, loader_args: Dict[str, Any]) -> List[Document]:
        """
        Load PDF documents from URLs or local paths.
        Downloads http(s) URLs to a temp file before loading.
        """
        docs: List[Document] = []
        urls: List[str] = loader_args.get("urls", [])

        for url in urls:
            tmp_path = None
            try:
                path_for_loader = url

                if isinstance(url, str) and url.strip().lower().startswith(("http://", "https://")):
                    parsed = urlparse(url.strip())
                    ext = Path(parsed.path).suffix.lower()
                    if ext != ".pdf":
                        logger.warning("Skipping non-PDF URL: %s", url)
                        continue

                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            resp.raise_for_status()
                            blob = await resp.read()

                    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
                    os.close(fd)
                    with open(tmp_path, "wb") as f:
                        f.write(blob)
                    path_for_loader = tmp_path

                loader = PyMuPDFLoader(file_path=path_for_loader)
                doc: List[Document] = await loader.aload()
                docs.extend(doc)
                logger.info("Successfully loaded PDF from %s", url)

            except FileNotFoundError:
                logger.error("File not found: %s", url)
            except ValueError as e:
                logger.error("Invalid path or unsupported input: %s – %s", url, e)
            except Exception as e:
                logger.exception("Failed to load %s: %s", url, e)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

        return docs
