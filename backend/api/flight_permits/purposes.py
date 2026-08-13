from django.db import models


class FlightPurpose(models.TextChoices):
    OPTION1 = "option_1", " 1. Geliştirme"
    OPTION2 = (
        "option_2",
        "2. Düzenlemelere veya sertifikasyon şartnamelerine uygunluğun gösterilmesi",
    )
    OPTION3 = "option_3", "3. Tasarım ya da üretim kuruluşlarının personel eğitimi"
    OPTION4 = "option_4", "4. Yeni üretilen hava araçlarında üretim uçuş testleri"
    OPTION5 = "option_5", "5. Üretim tesisleri arasında hava aracının uçurulması"
    OPTION6 = "option_6", "6. Müşteri kabulü için uçurulması"
    OPTION7 = "option_7", "7. Uçak teslimatı ve ihracı"
    OPTION8 = "option_8", "8. Yetkili makam tarafından kabul uçuşu yapılması"
    OPTION9 = "option_9", "9. Pazar araştırması, müşterinin personel eğitimi de dahil"
    OPTION10 = "option_10", "10. Sergiler ve hava gösterileri"
    OPTION11 = (
        "option_11",
        "11. Bakım veya uçuşa elverişlilik incelemesi için ya da depolama yerine uçurulması",
    )
    OPTION12 = (
        "option_12",
        "12. MTOW üzerinde, normal menzilin ötesi su veya karada (uygun iniş tesislerinin veya yakıtın bulunmadığı bölgelerde) aşırı yükle uçuş",
    )
    OPTION13 = "option_13", "13. Rekor kırma, hava yarışı veya benzeri yarışmalar"
    OPTION14 = (
        "option_14",
        "14. Çevresel gereksinimlere (gürültü, emisyon vb.) uyum sağlamadığı halde uçuşa elverişlilik gereksinimlerini karşılayan hava araçlarının uçurulması",
    )
    OPTION15 = (
        "option_15",
        "15. Sivil, bireysel ve kompleks olmayan hava araçlarında, UE sertifikası veya Restricted UE olmayan durumlarda ticari olmayan uçuş faaliyetleri",
    )
    OPTION16 = (
        "option_16",
        "16. Bakımdan sonra bir veya daha fazla sistem, parça ya da donanım işleyişinin test edilmesi veya sorun giderilme amacıyla uçuş",
    )


FLIGHT_PURPOSE_LABELS = dict(FlightPurpose.choices)


def flight_purpose_labels(values):
    return [FLIGHT_PURPOSE_LABELS[value] for value in values if value in FLIGHT_PURPOSE_LABELS]
