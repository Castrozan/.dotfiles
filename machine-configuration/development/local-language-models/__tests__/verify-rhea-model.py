import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import gguf
import numpy

specification = importlib.util.spec_from_file_location("rhea_model", sys.argv.pop(1))
rhea_model = importlib.util.module_from_spec(specification)
specification.loader.exec_module(rhea_model)


class RheaModelTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source_path = Path(self.directory.name) / "source.gguf"
        self.target_path = Path(self.directory.name) / "target.gguf"
        self.configuration_path = Path(self.directory.name) / "tokenizer.json"
        self.configuration_path.write_text(
            json.dumps({"chat_template": "<think></think><tool_call></tool_call>"})
        )

    def write_source(self, architecture="qwen3", last_token="||<|<|thinking_end|>"):
        vocabulary = [f"token_{index}" for index in range(151669)]
        vocabulary[151643:151646] = [
            "||<|<|endoftext|>",
            "||<|<|im_start|>",
            "||<|<|eos|>",
        ]
        vocabulary[151667:151669] = ["||<|<|thinking|>", last_token]
        writer = gguf.GGUFWriter(self.source_path, architecture)
        writer.add_token_list(vocabulary)
        writer.add_eos_token_id(151645)
        writer.add_chat_template("broken template")
        writer.add_array("test.labels", ["preserve", "metadata"])
        writer.add_uint64("test.counter", 2**40)
        writer.add_tensor("test.weights", numpy.arange(24, dtype=numpy.float32))
        writer.write_header_to_file()
        writer.write_kv_data_to_file()
        writer.write_tensors_to_file()
        writer.close()

    def materialize(self):
        rhea_model.materialize_rhea_model(
            self.source_path, self.configuration_path, self.target_path
        )

    def test_normalizes_protocol_and_preserves_model_data(self):
        self.write_source()
        self.materialize()
        source = gguf.GGUFReader(self.source_path)
        target = gguf.GGUFReader(self.target_path)
        vocabulary = target.fields["tokenizer.ggml.tokens"].contents()
        self.assertEqual(
            vocabulary[151643:151646], ["<|endoftext|>", "<|im_start|>", "<|im_end|>"]
        )
        self.assertEqual(vocabulary[151667:151669], ["<think>", "</think>"])
        self.assertEqual(vocabulary[151646], "token_151646")
        self.assertEqual(
            target.fields["tokenizer.ggml.eos_token_id"].contents(), 151645
        )
        self.assertEqual(
            target.fields["tokenizer.chat_template"].contents(),
            "<think></think><function-call></function-call>",
        )
        self.assertEqual(
            target.fields["test.labels"].contents(), ["preserve", "metadata"]
        )
        self.assertEqual(target.fields["test.counter"].contents(), 2**40)
        self.assertEqual(source.tensors[0].tensor_type, target.tensors[0].tensor_type)
        numpy.testing.assert_array_equal(source.tensors[0].data, target.tensors[0].data)

    def test_rejects_unexpected_special_token_before_writing(self):
        self.write_source(last_token="wrong token")
        with self.assertRaisesRegex(ValueError, "151668"):
            self.materialize()
        self.assertFalse(self.target_path.exists())

    def test_rejects_another_architecture_before_writing(self):
        self.write_source(architecture="llama")
        with self.assertRaisesRegex(ValueError, "qwen3"):
            self.materialize()
        self.assertFalse(self.target_path.exists())


if __name__ == "__main__":
    unittest.main()
