<script setup>
import { computed } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import { useWordToJira } from "../../../composables/useWordToJira";
import WordToJiraView from "../../../views/WordToJiraView.vue";

const { api, auth } = useAppContext();
const wordToJira = useWordToJira(api.apiFetch);
const canPublish = computed(() => Boolean(auth.currentUser.value?.is_staff));

function publish(draft) {
  if (!canPublish.value) return;
  wordToJira.publish(draft);
}
</script>

<template>
  <WordToJiraView
    :loading="wordToJira.parseLoading.value"
    :publishing="wordToJira.publishLoading.value"
    :error="wordToJira.error.value"
    :result="wordToJira.parseResult.value"
    :publish-result="wordToJira.publishResult.value"
    :can-publish="canPublish"
    @parse="wordToJira.parse"
    @publish="publish"
  />
</template>
