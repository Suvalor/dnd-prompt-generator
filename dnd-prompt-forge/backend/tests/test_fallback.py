"""
DND Prompt Forge - Fallback 生成器测试
覆盖 build_fallback_prompt 的各种场景
"""

import pytest
from services.fallback import build_fallback_prompt, STYLE_DESCRIPTIONS, MOOD_DESCRIPTIONS, AR, ANGLES


class TestBuildFallbackPrompt:
    """测试 fallback 提示词生成。"""

    def test_basic_portrait(self):
        """基本 portrait 类型应返回包含所有必需字段的字典。"""
        data = {
            "output_type": "portrait",
            "race": "Elf",
            "class_role": "Ranger",
            "style": "painterly",
            "mood": "heroic",
            "description": "A stoic forest guardian",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "main_prompt" in result
        assert "short_prompt" in result
        assert "negative_prompt" in result
        assert "style_notes" in result
        assert "usage_tip" in result
        assert len(result) == 5

    def test_portrait_content(self):
        """portrait 类型主提示词应包含正确内容。"""
        data = {
            "output_type": "portrait",
            "race": "Tiefling",
            "class_role": "Warlock",
            "style": "grimdark",
            "mood": "menacing",
            "description": "dark pact",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        main = result["main_prompt"]
        assert "Tiefling" in main
        assert "Warlock" in main
        assert "dark pact" in main
        assert "--ar 4:5" in main

    def test_token_output(self):
        """token 类型应包含 top-down 和 1:1 比例。"""
        data = {
            "output_type": "token",
            "race": "Human",
            "class_role": "Fighter",
            "style": "ink",
            "mood": "serene",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "top-down" in result["main_prompt"]
        assert "--ar 1:1" in result["main_prompt"]
        assert result["usage_tip"]  # token 有特定的 usage_tip

    def test_scene_output(self):
        """scene 类型应包含环境描述。"""
        data = {
            "output_type": "scene",
            "race": "Tavern",
            "class_role": "",
            "style": "painterly",
            "mood": "mystical",
            "description": "cozy interior",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "wide environment" in result["main_prompt"]
        assert "--ar 16:9" in result["main_prompt"]

    def test_fullbody_output(self):
        """fullbody 类型应包含全身描述。"""
        data = {
            "output_type": "fullbody",
            "race": "Dwarf",
            "class_role": "Paladin",
            "style": "realism",
            "mood": "heroic",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "full-body" in result["main_prompt"]
        assert "--ar 2:3" in result["main_prompt"]

    def test_monster_output(self):
        """monster 类型应包含 creature 描述。"""
        data = {
            "output_type": "monster",
            "race": "Dragon",
            "class_role": "",
            "style": "comic",
            "mood": "menacing",
            "description": "ancient red",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "creature" in result["main_prompt"]
        assert "--ar 3:2" in result["main_prompt"]

    def test_npc_output(self):
        """npc 类型应包含 character portrait。"""
        data = {
            "output_type": "npc",
            "race": "Halfling",
            "class_role": "Bard",
            "style": "storybook",
            "mood": "serene",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "character portrait" in result["main_prompt"]
        assert "--ar 4:5" in result["main_prompt"]

    def test_sd_model_suffix(self):
        """SD 模型应添加特定前缀。"""
        data = {
            "output_type": "portrait",
            "race": "Elf",
            "class_role": "Wizard",
            "style": "painterly",
            "mood": "mystical",
            "description": "",
            "target_model": "sd",
        }
        result = build_fallback_prompt(data)
        assert result["main_prompt"].startswith("(masterpiece, best quality, highly detailed:1.2)")

    def test_unknown_output_type(self):
        """未知 output_type 应回退到通用处理。"""
        data = {
            "output_type": "unknown",
            "race": "Elf",
            "class_role": "Wizard",
            "style": "painterly",
            "mood": "mystical",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "main_prompt" in result
        assert "short_prompt" in result

    def test_empty_subject(self):
        """空 race/class 时应使用默认描述。"""
        data = {
            "output_type": "portrait",
            "race": "",
            "class_role": "",
            "style": "painterly",
            "mood": "brooding",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "fantasy character" in result["main_prompt"]

    def test_optional_fields(self):
        """可选字段（alignment, weapon, armor, magic, palette, camera, gender, age）应被包含。"""
        data = {
            "output_type": "portrait",
            "race": "Elf",
            "class_role": "Ranger",
            "style": "painterly",
            "mood": "heroic",
            "description": "",
            "target_model": "midjourney",
            "alignment": "Lawful Good",
            "weapon": "longbow",
            "armor": "leather armor",
            "magic": "nature",
            "palette": "emerald green",
            "gender": "female",
            "age": "young adult",
        }
        result = build_fallback_prompt(data)
        main = result["main_prompt"]
        assert "Lawful Good" in main
        assert "longbow" in main
        assert "leather armor" in main
        assert "nature" in main
        assert "emerald green" in main

    def test_empty_scene_subject(self):
        """scene 类型空 race 时应使用默认描述。"""
        data = {
            "output_type": "scene",
            "race": "",
            "class_role": "",
            "style": "painterly",
            "mood": "mystical",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert "fantasy location" in result["main_prompt"]

    def test_negative_prompt_content(self):
        """负面提示词应包含基础负面词和类型特定词。"""
        data = {
            "output_type": "token",
            "race": "Human",
            "class_role": "Fighter",
            "style": "painterly",
            "mood": "heroic",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        neg = result["negative_prompt"]
        assert "blurry" in neg
        assert "lowres" in neg
        assert "background clutter" in neg

    def test_realism_negative(self):
        """realism 风格应添加额外的负面词。"""
        data = {
            "output_type": "portrait",
            "race": "Elf",
            "class_role": "Wizard",
            "style": "realism",
            "mood": "mystical",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        neg = result["negative_prompt"]
        assert "painting" in neg
        assert "illustration" in neg

    def test_style_notes_per_type(self):
        """每种 output_type 应有对应的 style_notes。"""
        for output_type in ["portrait", "fullbody", "token", "npc", "monster", "scene"]:
            data = {
                "output_type": output_type,
                "race": "Elf",
                "class_role": "Wizard",
                "style": "painterly",
                "mood": "mystical",
                "description": "",
                "target_model": "midjourney",
            }
            result = build_fallback_prompt(data)
            assert result["style_notes"] != "", f"style_notes should not be empty for {output_type}"

    def test_short_prompt_content(self):
        """短提示词应包含基本信息。"""
        data = {
            "output_type": "portrait",
            "race": "Elf",
            "class_role": "Ranger",
            "style": "painterly",
            "mood": "heroic",
            "description": "forest guardian",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        short = result["short_prompt"]
        assert "Elf" in short
        assert "Ranger" in short
        assert "painterly" in short

    def test_return_type(self):
        """返回值应为包含 5 个键的字典。"""
        data = {
            "output_type": "portrait",
            "race": "Elf",
            "class_role": "Wizard",
            "style": "painterly",
            "mood": "mystical",
            "description": "",
            "target_model": "midjourney",
        }
        result = build_fallback_prompt(data)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"main_prompt", "short_prompt", "negative_prompt", "style_notes", "usage_tip"}
