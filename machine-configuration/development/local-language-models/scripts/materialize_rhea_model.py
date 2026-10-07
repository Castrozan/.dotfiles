import json
import sys
from pathlib import Path

import gguf


def materialize_rhea_model(source_path, tokenizer_configuration_path, target_path):
    reader = gguf.GGUFReader(source_path)
    architecture = reader.fields["general.architecture"].contents()
    if architecture != "qwen3":
        raise ValueError("Rhea requires the qwen3 architecture")
    vocabulary = reader.fields["tokenizer.ggml.tokens"].contents()
    canonical_tokens = (
        (151643, "||<|<|endoftext|>", "<|endoftext|>"),
        (151644, "||<|<|im_start|>", "<|im_start|>"),
        (151645, "||<|<|eos|>", "<|im_end|>"),
        (151667, "||<|<|thinking|>", "<think>"),
        (151668, "||<|<|thinking_end|>", "</think>"),
    )
    for token_id, expected_token, canonical_token in canonical_tokens:
        if token_id >= len(vocabulary) or vocabulary[token_id] != expected_token:
            raise ValueError(f"Unexpected Rhea special token at {token_id}")
        vocabulary[token_id] = canonical_token
    tokenizer_configuration = json.loads(Path(tokenizer_configuration_path).read_text())
    chat_template = (
        tokenizer_configuration["chat_template"]
        .replace("<tool_call>", "<function-call>")
        .replace("</tool_call>", "</function-call>")
    )
    metadata = {
        "tokenizer.ggml.tokens": vocabulary,
        "tokenizer.chat_template": chat_template,
    }
    writer = gguf.GGUFWriter(target_path, architecture, endianess=reader.endianess)
    for field in reader.fields.values():
        if field.name == "general.architecture" or field.name.startswith("GGUF."):
            continue
        value_type = field.types[0]
        array_type = field.types[-1] if value_type == gguf.GGUFValueType.ARRAY else None
        writer.add_key_value(
            field.name,
            metadata.get(field.name, field.contents()),
            value_type,
            sub_type=array_type,
        )
    for tensor in reader.tensors:
        writer.add_tensor_info(
            tensor.name,
            tensor.data.shape,
            tensor.data.dtype,
            tensor.data.nbytes,
            tensor.tensor_type,
        )
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_ti_data_to_file()
    for tensor in reader.tensors:
        writer.write_tensor_data(tensor.data)
    writer.close()


if __name__ == "__main__":
    materialize_rhea_model(*sys.argv[1:])
