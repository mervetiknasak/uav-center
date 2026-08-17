<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const activeSection = computed(() =>
  route.name === "flight-permits" ? "flight-permits" : "form-processes"
);

function navigate(section) {
  if (section !== activeSection.value) router.push({ name: section });
}
</script>

<template>
  <n-tabs
    class="process-app-navigation"
    type="segment"
    :value="activeSection"
    @update:value="navigate"
  >
    <n-tab name="form-processes">Formlar</n-tab>
    <n-tab name="flight-permits">Uçuş İzinleri</n-tab>
  </n-tabs>
</template>
