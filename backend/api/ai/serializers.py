from django.conf import settings
from rest_framework import serializers


class OllamaChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant", "tool"])
    content = serializers.CharField(max_length=120_000, allow_blank=True, trim_whitespace=False)
    thinking = serializers.CharField(
        max_length=120_000, required=False, allow_blank=True, trim_whitespace=False
    )
    images = serializers.ListField(
        child=serializers.CharField(trim_whitespace=False),
        required=False,
        max_length=3,
    )
    tool_calls = serializers.JSONField(required=False)
    tool_name = serializers.CharField(max_length=120, required=False)

    def validate_images(self, images):
        total_size = sum(len(image) for image in images)
        if total_size > 28_000_000:
            raise serializers.ValidationError("Görsel verisi 20 MB sınırını aşıyor.")
        for image in images:
            if image.startswith("data:") and "," not in image:
                raise serializers.ValidationError("Geçersiz data URL görseli.")
        return [image.split(",", 1)[-1] if image.startswith("data:") else image for image in images]


class OllamaChatRequestSerializer(serializers.Serializer):
    model = serializers.CharField(max_length=160, required=False)
    messages = OllamaChatMessageSerializer(many=True, allow_empty=False, max_length=60)
    system_prompt = serializers.CharField(
        max_length=20_000, required=False, allow_blank=True, trim_whitespace=False
    )
    think = serializers.BooleanField(default=True)
    response_format = serializers.ChoiceField(
        choices=["text", "json"], default="text", required=False
    )
    tools = serializers.JSONField(required=False, default=list)
    temperature = serializers.FloatField(min_value=0, max_value=2, default=1.0)
    top_p = serializers.FloatField(min_value=0, max_value=1, default=0.95)
    top_k = serializers.IntegerField(min_value=0, max_value=200, default=64)
    num_ctx = serializers.IntegerField(min_value=512, max_value=131_072, default=8192)
    num_predict = serializers.IntegerField(min_value=-1, max_value=32_768, default=2048)
    seed = serializers.IntegerField(required=False, allow_null=True)
    keep_alive = serializers.RegexField(regex=r"^(?:0|\d+[smh])$", default="5m", required=False)

    def validate_tools(self, tools):
        if not isinstance(tools, list):
            raise serializers.ValidationError("Araç şeması bir JSON listesi olmalıdır.")
        if len(tools) > 20:
            raise serializers.ValidationError("En fazla 20 araç tanımlanabilir.")
        return tools

    def to_ollama_payload(self):
        data = self.validated_data
        messages = list(data["messages"])
        system_prompt = data.get("system_prompt", "").strip()
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        options = {
            "temperature": data["temperature"],
            "top_p": data["top_p"],
            "top_k": data["top_k"],
            "num_ctx": data["num_ctx"],
            "num_predict": data["num_predict"],
        }
        if data.get("seed") is not None:
            options["seed"] = data["seed"]

        payload = {
            "model": data.get("model") or settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": True,
            "think": data["think"],
            "keep_alive": data["keep_alive"],
            "options": options,
        }
        if data.get("response_format") == "json":
            payload["format"] = "json"
        if data.get("tools"):
            payload["tools"] = data["tools"]
        return payload
