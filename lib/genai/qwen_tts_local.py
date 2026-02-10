from pathlib import Path
from enum import Enum
from typing import List, Dict, Union, Any, Optional

import torch
import numpy as np


# CUDA_VISIBLE_DEVICES=0
torch.backends.cuda.matmul.allow_tf32 = True 
torch.backends.cudnn.allow_tf32 = True 

import soundfile as sf
from qwen_tts import Qwen3TTSModel

class ATTENTION_TYPE(Enum):
    EAGER = "eager"
    FLASH_ATTENTION_2 = "flash_attention_2"
    SDPA = "sdpa"

class Qwen3TTS:
    def __init__(self, 
                 model_name: str="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", 
                 device: str = "cuda:0", 
                 attention_type: ATTENTION_TYPE=ATTENTION_TYPE.FLASH_ATTENTION_2
        ):

        self.model_name = model_name
        self.device = device
        self.attention_type = attention_type.value

        self.model = Qwen3TTSModel.from_pretrained(
            self.model_name,
            device_map=self.device,
            dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            attn_implementation=self.attention_type
        )

    def generate(self, 
            file_name: Path, 
            text: List[str], 
            language: List[str], 
            speaker: List[str], 
            instruct: List[str]=None
        ):
        
        wavs, sr = self._generate_voice(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct
        )

        self._save_audio(
            filename=file_name,
            audio_list=wavs,
            sample_rate=sr
        )
    
    def _generate_voice(self, 
                        text: List[str], 
                        language: List[str], 
                        speaker: List[str], 
                        instruct: List[str]=None
        ):

        wavs, sr = self.model.generate_custom_voice(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct
        )

        return wavs, sr

    def _save_audio(self, filename, audio_list, sample_rate):
        combined = np.concatenate(audio_list, axis=0)
        sf.write(filename, combined, sample_rate)

