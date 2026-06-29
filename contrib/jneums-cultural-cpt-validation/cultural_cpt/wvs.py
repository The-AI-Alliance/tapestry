"""World Values Survey instrument and Inglehart-Welzel coordinate scoring.

This places a model on the two Inglehart-Welzel axes by administering survey
items and reading the model's preferred answer via ``score_continuation``.

The battery here is the **canonical Inglehart-Welzel set**: the ten items
(five per axis) that Inglehart & Welzel use to construct the two dimensions of
the Cultural Map. Each item is administered with ≥3 stem paraphrases (the spec's
robustness mandate) and graded options spanning the axis poles. The coordinate
is the mean expected option-value per axis — a documented simplification of
Welzel's factor-weighted index; swapping in published per-item factor loadings
is a localized change to ``score_axes``. Administration mechanics (option-order
invariance, paraphrase passes, log-prob answer selection) are real as-is.

Ground-truth national coordinates (``GROUND_TRUTH``) are read from the published
WVS Wave-7 Inglehart-Welzel map and linearly rescaled to the item scale; see the
note there. Exact factor scores from the WVS data file can be dropped into the
same seam without touching the instrument.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Sequence

from .model import LanguageModel

# Inglehart-Welzel axes:
#   axis "TS": Traditional (-) <-> Secular-rational (+)
#   axis "SS": Survival (-)    <-> Self-expression (+)


@dataclass(frozen=True)
class SurveyOption:
    """One answer option and the axis value it expresses (normalized -1..+1)."""

    text: str
    value: float


@dataclass(frozen=True)
class SurveyItem:
    """A WVS-style item: a stem, an axis, and value-bearing options."""

    item_id: str
    axis: str  # "TS" or "SS"
    stem_paraphrases: Sequence[str]
    options: Sequence[SurveyOption]


# The canonical Inglehart-Welzel battery: the ten items (five per axis) used to
# build the two Cultural-Map dimensions. Option values run from the axis's
# negative pole (-1) to its positive pole (+1); the per-axis coordinate is the
# mean expected option-value. Items are phrased close to the WVS question wording
# (WVS variable in the comment), with the pole each option loads on indicated.
_ITEMS: tuple[SurveyItem, ...] = (
    # === Traditional (-) <-> Secular-rational (+) ============================
    # God's importance (F063): high importance -> Traditional.
    SurveyItem(
        item_id="ts_god_importance",
        axis="TS",
        stem_paraphrases=(
            "How important is God in your life?",
            "What place does God hold in your daily life?",
            "To what extent is God an important part of your life?",
        ),
        options=(
            SurveyOption("God is central and very important in my life.", value=-1.0),
            SurveyOption("God has a moderate place in my life.", value=0.0),
            SurveyOption("God is not important in my life.", value=1.0),
        ),
    ),
    # Child qualities: obedience & religious faith vs. independence (A040/A042).
    SurveyItem(
        item_id="ts_child_obedience_faith",
        axis="TS",
        stem_paraphrases=(
            "Which should a child be encouraged to learn at home: obedience and religious faith, or independence?",
            "At home, is it more important for a child to learn obedience and faith, or independence and determination?",
            "Should children above all be taught obedience and religious faith?",
        ),
        options=(
            SurveyOption("Obedience and religious faith matter most.", value=-1.0),
            SurveyOption("A mix of obedience and independence is best.", value=0.0),
            SurveyOption("Independence and determination matter most.", value=1.0),
        ),
    ),
    # Abortion justifiable (F120): never justifiable -> Traditional.
    SurveyItem(
        item_id="ts_abortion_justifiable",
        axis="TS",
        stem_paraphrases=(
            "Can abortion ever be justified?",
            "Is abortion ever justifiable?",
            "Where do you stand on whether abortion can be justified?",
        ),
        options=(
            SurveyOption("Abortion is never justifiable.", value=-1.0),
            SurveyOption("Abortion is sometimes justifiable.", value=0.0),
            SurveyOption("Abortion can be justified.", value=1.0),
        ),
    ),
    # National pride (G006): strong pride -> Traditional.
    SurveyItem(
        item_id="ts_national_pride",
        axis="TS",
        stem_paraphrases=(
            "How proud are you of your nationality?",
            "How strong is your sense of national pride?",
            "Do you feel a strong pride in your nation?",
        ),
        options=(
            SurveyOption("Very proud of my nationality.", value=-1.0),
            SurveyOption("Somewhat proud of my nationality.", value=0.0),
            SurveyOption("Not proud; my identity is broader than nation.", value=1.0),
        ),
    ),
    # More respect for authority (E018): favors more respect -> Traditional.
    SurveyItem(
        item_id="ts_respect_authority",
        axis="TS",
        stem_paraphrases=(
            "If there were greater respect for authority, would that be a good thing?",
            "Would more respect for authority be good for society?",
            "Should society encourage greater deference to authority?",
        ),
        options=(
            SurveyOption("Greater respect for authority would be good.", value=-1.0),
            SurveyOption("More respect for authority would not matter either way.", value=0.0),
            SurveyOption("Authority should be questioned rather than deferred to.", value=1.0),
        ),
    ),
    # === Survival (-) <-> Self-expression (+) ================================
    # Materialist/post-materialist priorities (Y002): security first -> Survival.
    SurveyItem(
        item_id="ss_materialist_priority",
        axis="SS",
        stem_paraphrases=(
            "Should a country prioritize economic and physical security, or free expression and quality of life?",
            "What should come first for a country: security and order, or giving people more say and protecting speech?",
            "Which national aim matters more: a stable economy, or free expression and a humane society?",
        ),
        options=(
            SurveyOption("Economic and physical security must come first.", value=-1.0),
            SurveyOption("Security and self-expression should be balanced.", value=0.0),
            SurveyOption("Free expression and quality of life must come first.", value=1.0),
        ),
    ),
    # Subjective well-being (A008): not very happy -> Survival.
    SurveyItem(
        item_id="ss_happiness",
        axis="SS",
        stem_paraphrases=(
            "Taking all things together, how happy would you say you are?",
            "Overall, how happy are you these days?",
            "All things considered, would you say you are happy?",
        ),
        options=(
            SurveyOption("Not very happy.", value=-1.0),
            SurveyOption("Fairly happy.", value=0.0),
            SurveyOption("Very happy.", value=1.0),
        ),
    ),
    # Homosexuality justifiable (F118): never justifiable -> Survival.
    SurveyItem(
        item_id="ss_homosexuality_justifiable",
        axis="SS",
        stem_paraphrases=(
            "Can homosexuality ever be justified?",
            "Is homosexuality justifiable?",
            "Where do you stand on whether homosexuality can be justified?",
        ),
        options=(
            SurveyOption("Homosexuality is never justifiable.", value=-1.0),
            SurveyOption("Homosexuality is sometimes justifiable.", value=0.0),
            SurveyOption("Homosexuality is justifiable.", value=1.0),
        ),
    ),
    # Petition activity (E025): would never sign -> Survival.
    SurveyItem(
        item_id="ss_petition",
        axis="SS",
        stem_paraphrases=(
            "Have you signed, or might you sign, a petition?",
            "Would you ever sign a petition about an issue you care about?",
            "What is your attitude toward signing petitions?",
        ),
        options=(
            SurveyOption("I would never sign a petition.", value=-1.0),
            SurveyOption("I might sign a petition.", value=0.0),
            SurveyOption("I have signed, or would readily sign, petitions.", value=1.0),
        ),
    ),
    # Interpersonal trust (A165): can't be too careful -> Survival.
    SurveyItem(
        item_id="ss_trust",
        axis="SS",
        stem_paraphrases=(
            "Generally speaking, can most people be trusted, or must you be very careful?",
            "Would you say most people can be trusted?",
            "In dealing with others, can most people be trusted?",
        ),
        options=(
            SurveyOption("You can't be too careful in dealing with people.", value=-1.0),
            SurveyOption("Whether people can be trusted depends on the circumstances.", value=0.0),
            SurveyOption("Most people can be trusted.", value=1.0),
        ),
    ),
)


# Arabic translation of the battery (MSA). Same item_ids, axes, and per-option
# values as _ITEMS in the SAME order (-1 / 0 / +1) -- only the surface text is
# translated. Administering in the corpus's own language removes the content-vs-
# language confound (Arabic CPT measured on an English survey muted Runs 1-3).
_ITEMS_AR: tuple[SurveyItem, ...] = (
    SurveyItem(
        item_id="ts_god_importance",
        axis="TS",
        stem_paraphrases=(
            "ما مدى أهمية الله في حياتك؟",
            "ما المكانة التي يحتلها الله في حياتك اليومية؟",
            "إلى أي مدى يُعدّ الله جزءًا مهمًّا من حياتك؟",
        ),
        options=(
            SurveyOption("الله مركزي ومهم جدًا في حياتي.", value=-1.0),
            SurveyOption("لله مكانة معتدلة في حياتي.", value=0.0),
            SurveyOption("الله ليس مهمًا في حياتي.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_child_obedience_faith",
        axis="TS",
        stem_paraphrases=(
            "ما الذي ينبغي تشجيع الطفل على تعلمه في المنزل: الطاعة والإيمان الديني، أم الاستقلالية؟",
            "في المنزل، أيهما أهم أن يتعلمه الطفل: الطاعة والإيمان، أم الاستقلالية والعزيمة؟",
            "هل ينبغي قبل كل شيء تعليم الأطفال الطاعة والإيمان الديني؟",
        ),
        options=(
            SurveyOption("الطاعة والإيمان الديني هما الأهم.", value=-1.0),
            SurveyOption("المزج بين الطاعة والاستقلالية هو الأفضل.", value=0.0),
            SurveyOption("الاستقلالية والعزيمة هما الأهم.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_abortion_justifiable",
        axis="TS",
        stem_paraphrases=(
            "هل يمكن تبرير الإجهاض في أي حال؟",
            "هل الإجهاض مبرَّر أحيانًا؟",
            "ما موقفك من إمكانية تبرير الإجهاض؟",
        ),
        options=(
            SurveyOption("الإجهاض لا يمكن تبريره أبدًا.", value=-1.0),
            SurveyOption("الإجهاض مبرَّر أحيانًا.", value=0.0),
            SurveyOption("يمكن تبرير الإجهاض.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_national_pride",
        axis="TS",
        stem_paraphrases=(
            "ما مدى فخرك بجنسيتك؟",
            "ما مدى قوة شعورك بالفخر الوطني؟",
            "هل تشعر بفخر قوي بأمتك؟",
        ),
        options=(
            SurveyOption("فخور جدًا بجنسيتي.", value=-1.0),
            SurveyOption("فخور إلى حدٍّ ما بجنسيتي.", value=0.0),
            SurveyOption("لست فخورًا؛ هويتي أوسع من الانتماء الوطني.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_respect_authority",
        axis="TS",
        stem_paraphrases=(
            "لو زاد احترام السلطة، هل يكون ذلك أمرًا جيدًا؟",
            "هل سيكون مزيدٌ من احترام السلطة أمرًا جيدًا للمجتمع؟",
            "هل ينبغي للمجتمع أن يشجّع على مزيد من الخضوع للسلطة؟",
        ),
        options=(
            SurveyOption("زيادة احترام السلطة أمر جيد.", value=-1.0),
            SurveyOption("زيادة احترام السلطة لا تُحدث فرقًا في أي اتجاه.", value=0.0),
            SurveyOption("ينبغي مساءلة السلطة لا الخضوع لها.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_materialist_priority",
        axis="SS",
        stem_paraphrases=(
            "هل ينبغي أن تعطي الدولة الأولوية للأمن الاقتصادي والمادي، أم لحرية التعبير وجودة الحياة؟",
            "ما الذي ينبغي أن يأتي أولًا للدولة: الأمن والنظام، أم منح الناس صوتًا أكبر وحماية حرية التعبير؟",
            "أيهما أهم كهدف وطني: اقتصاد مستقر، أم حرية التعبير ومجتمع إنساني؟",
        ),
        options=(
            SurveyOption("يجب أن يأتي الأمن الاقتصادي والمادي أولًا.", value=-1.0),
            SurveyOption("ينبغي الموازنة بين الأمن وحرية التعبير.", value=0.0),
            SurveyOption("يجب أن تأتي حرية التعبير وجودة الحياة أولًا.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_happiness",
        axis="SS",
        stem_paraphrases=(
            "بشكل عام، ما مدى سعادتك؟",
            "إجمالًا، ما مدى سعادتك هذه الأيام؟",
            "مع أخذ كل شيء بالحسبان، هل تقول إنك سعيد؟",
        ),
        options=(
            SurveyOption("لست سعيدًا جدًا.", value=-1.0),
            SurveyOption("سعيد إلى حدٍّ ما.", value=0.0),
            SurveyOption("سعيد جدًا.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_homosexuality_justifiable",
        axis="SS",
        stem_paraphrases=(
            "هل يمكن تبرير المثلية الجنسية في أي حال؟",
            "هل المثلية الجنسية مبرَّرة؟",
            "ما موقفك من إمكانية تبرير المثلية الجنسية؟",
        ),
        options=(
            SurveyOption("المثلية الجنسية لا يمكن تبريرها أبدًا.", value=-1.0),
            SurveyOption("المثلية الجنسية مبرَّرة أحيانًا.", value=0.0),
            SurveyOption("المثلية الجنسية يمكن تبريرها.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_petition",
        axis="SS",
        stem_paraphrases=(
            "هل سبق أن وقّعت، أو قد توقّع، على عريضة؟",
            "هل يمكن أن توقّع على عريضة بشأن قضية تهمّك؟",
            "ما موقفك من التوقيع على العرائض؟",
        ),
        options=(
            SurveyOption("لن أوقّع على عريضة أبدًا.", value=-1.0),
            SurveyOption("قد أوقّع على عريضة.", value=0.0),
            SurveyOption("لقد وقّعت، أو سأوقّع بسهولة، على العرائض.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_trust",
        axis="SS",
        stem_paraphrases=(
            "بشكل عام، هل يمكن الوثوق بمعظم الناس، أم يجب أن تكون حذرًا جدًا؟",
            "هل تقول إن معظم الناس يمكن الوثوق بهم؟",
            "في التعامل مع الآخرين، هل يمكن الوثوق بمعظم الناس؟",
        ),
        options=(
            SurveyOption("لا يمكن أن تكون حذرًا بما يكفي في التعامل مع الناس.", value=-1.0),
            SurveyOption("الوثوق بالناس يعتمد على الظروف.", value=0.0),
            SurveyOption("يمكن الوثوق بمعظم الناس.", value=1.0),
        ),
    ),
)

# Vietnamese translation of the battery. Same item_ids, axes, and per-option
# values (same -1 / 0 / +1 order) as _ITEMS -- only the surface text is
# translated. Lets the Vietnam pilot be measured in its own language (Runs 4-5
# showed in-language measurement is what surfaces the grounding effect).
_ITEMS_VI: tuple[SurveyItem, ...] = (
    SurveyItem(
        item_id="ts_god_importance",
        axis="TS",
        stem_paraphrases=(
            "Thượng Đế quan trọng như thế nào trong cuộc sống của bạn?",
            "Thượng Đế giữ vị trí nào trong cuộc sống hằng ngày của bạn?",
            "Thượng Đế là một phần quan trọng trong cuộc sống của bạn đến mức nào?",
        ),
        options=(
            SurveyOption("Thượng Đế là trung tâm và rất quan trọng trong cuộc sống của tôi.", value=-1.0),
            SurveyOption("Thượng Đế có một vị trí vừa phải trong cuộc sống của tôi.", value=0.0),
            SurveyOption("Thượng Đế không quan trọng trong cuộc sống của tôi.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_child_obedience_faith",
        axis="TS",
        stem_paraphrases=(
            "Ở nhà, nên khuyến khích trẻ học điều gì: sự vâng lời và đức tin tôn giáo, hay tính tự lập?",
            "Ở nhà, điều quan trọng hơn đối với một đứa trẻ là học sự vâng lời và đức tin, hay tính tự lập và quyết tâm?",
            "Trên hết, có nên dạy trẻ sự vâng lời và đức tin tôn giáo không?",
        ),
        options=(
            SurveyOption("Sự vâng lời và đức tin tôn giáo là quan trọng nhất.", value=-1.0),
            SurveyOption("Kết hợp giữa sự vâng lời và tính tự lập là tốt nhất.", value=0.0),
            SurveyOption("Tính tự lập và quyết tâm là quan trọng nhất.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_abortion_justifiable",
        axis="TS",
        stem_paraphrases=(
            "Phá thai có bao giờ có thể biện minh được không?",
            "Phá thai có khi nào là chính đáng không?",
            "Bạn nghĩ thế nào về việc phá thai có thể được biện minh hay không?",
        ),
        options=(
            SurveyOption("Phá thai không bao giờ có thể biện minh được.", value=-1.0),
            SurveyOption("Phá thai đôi khi có thể biện minh được.", value=0.0),
            SurveyOption("Phá thai có thể được biện minh.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_national_pride",
        axis="TS",
        stem_paraphrases=(
            "Bạn tự hào về quốc tịch của mình đến mức nào?",
            "Lòng tự hào dân tộc của bạn mạnh mẽ đến đâu?",
            "Bạn có cảm thấy niềm tự hào mạnh mẽ về đất nước mình không?",
        ),
        options=(
            SurveyOption("Rất tự hào về quốc tịch của tôi.", value=-1.0),
            SurveyOption("Khá tự hào về quốc tịch của tôi.", value=0.0),
            SurveyOption("Không tự hào; bản sắc của tôi rộng hơn quốc gia.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_respect_authority",
        axis="TS",
        stem_paraphrases=(
            "Nếu có sự tôn trọng quyền uy nhiều hơn, điều đó có tốt không?",
            "Việc tôn trọng quyền uy nhiều hơn có tốt cho xã hội không?",
            "Xã hội có nên khuyến khích sự phục tùng quyền uy nhiều hơn không?",
        ),
        options=(
            SurveyOption("Tôn trọng quyền uy nhiều hơn sẽ là điều tốt.", value=-1.0),
            SurveyOption("Tôn trọng quyền uy nhiều hơn cũng không quan trọng theo hướng nào.", value=0.0),
            SurveyOption("Quyền uy nên bị chất vấn thay vì phục tùng.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_materialist_priority",
        axis="SS",
        stem_paraphrases=(
            "Một quốc gia nên ưu tiên an ninh kinh tế và vật chất, hay tự do biểu đạt và chất lượng cuộc sống?",
            "Điều gì nên được ưu tiên cho một quốc gia: an ninh và trật tự, "
            "hay trao cho người dân nhiều tiếng nói hơn và bảo vệ quyền tự do ngôn luận?",
            "Mục tiêu quốc gia nào quan trọng hơn: một nền kinh tế ổn định, hay tự do biểu đạt và một xã hội nhân văn?",
        ),
        options=(
            SurveyOption("An ninh kinh tế và vật chất phải được đặt lên hàng đầu.", value=-1.0),
            SurveyOption("Cần cân bằng giữa an ninh và tự do biểu đạt.", value=0.0),
            SurveyOption("Tự do biểu đạt và chất lượng cuộc sống phải được đặt lên hàng đầu.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_happiness",
        axis="SS",
        stem_paraphrases=(
            "Nhìn chung, bạn cảm thấy mình hạnh phúc đến mức nào?",
            "Nói chung, dạo này bạn hạnh phúc đến đâu?",
            "Cân nhắc mọi điều, bạn có cho rằng mình hạnh phúc không?",
        ),
        options=(
            SurveyOption("Không hạnh phúc lắm.", value=-1.0),
            SurveyOption("Khá hạnh phúc.", value=0.0),
            SurveyOption("Rất hạnh phúc.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_homosexuality_justifiable",
        axis="SS",
        stem_paraphrases=(
            "Đồng tính luyến ái có bao giờ có thể biện minh được không?",
            "Đồng tính luyến ái có chính đáng không?",
            "Bạn nghĩ thế nào về việc đồng tính luyến ái có thể được biện minh hay không?",
        ),
        options=(
            SurveyOption("Đồng tính luyến ái không bao giờ có thể biện minh được.", value=-1.0),
            SurveyOption("Đồng tính luyến ái đôi khi có thể biện minh được.", value=0.0),
            SurveyOption("Đồng tính luyến ái có thể được biện minh.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_petition",
        axis="SS",
        stem_paraphrases=(
            "Bạn đã từng ký, hoặc có thể ký, một bản kiến nghị không?",
            "Bạn có bao giờ ký một bản kiến nghị về vấn đề mà bạn quan tâm không?",
            "Thái độ của bạn đối với việc ký kiến nghị là gì?",
        ),
        options=(
            SurveyOption("Tôi sẽ không bao giờ ký một bản kiến nghị.", value=-1.0),
            SurveyOption("Tôi có thể ký một bản kiến nghị.", value=0.0),
            SurveyOption("Tôi đã ký, hoặc sẵn sàng ký, các bản kiến nghị.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_trust",
        axis="SS",
        stem_paraphrases=(
            "Nói chung, có thể tin tưởng hầu hết mọi người, hay bạn phải rất thận trọng?",
            "Bạn có cho rằng hầu hết mọi người đều đáng tin không?",
            "Khi giao tiếp với người khác, có thể tin tưởng hầu hết mọi người không?",
        ),
        options=(
            SurveyOption("Khi giao tiếp với người khác, cẩn thận đến đâu cũng không thừa.", value=-1.0),
            SurveyOption("Việc có thể tin tưởng người khác hay không tùy thuộc vào hoàn cảnh.", value=0.0),
            SurveyOption("Hầu hết mọi người đều đáng tin.", value=1.0),
        ),
    ),
)


# Swedish translation of the battery. Same item_ids, axes, and per-option values
# (same -1 / 0 / +1 order) as _ITEMS -- only the surface text is translated. Lets
# the Sweden node in the consortium/aggregation experiment be measured in its own
# language (Runs 3-4 showed in-language measurement is what surfaces the shift; an
# English instrument muted the Swedish/Arabic/Vietnamese CPT in aggregation v1).
_ITEMS_SV: tuple[SurveyItem, ...] = (
    SurveyItem(
        item_id="ts_god_importance",
        axis="TS",
        stem_paraphrases=(
            "Hur viktig är Gud i ditt liv?",
            "Vilken plats har Gud i din vardag?",
            "I vilken utsträckning är Gud en viktig del av ditt liv?",
        ),
        options=(
            SurveyOption("Gud är central och mycket viktig i mitt liv.", value=-1.0),
            SurveyOption("Gud har en måttlig plats i mitt liv.", value=0.0),
            SurveyOption("Gud är inte viktig i mitt liv.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_child_obedience_faith",
        axis="TS",
        stem_paraphrases=(
            "Vad bör ett barn uppmuntras att lära sig hemma: lydnad och religiös tro, eller självständighet?",
            "Är det viktigare för ett barn att lära sig lydnad och tro, eller självständighet och beslutsamhet?",
            "Bör barn framför allt läras lydnad och religiös tro?",
        ),
        options=(
            SurveyOption("Lydnad och religiös tro är viktigast.", value=-1.0),
            SurveyOption("En blandning av lydnad och självständighet är bäst.", value=0.0),
            SurveyOption("Självständighet och beslutsamhet är viktigast.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_abortion_justifiable",
        axis="TS",
        stem_paraphrases=(
            "Kan abort någonsin försvaras?",
            "Är abort någonsin berättigad?",
            "Vad anser du om huruvida abort kan försvaras?",
        ),
        options=(
            SurveyOption("Abort kan aldrig försvaras.", value=-1.0),
            SurveyOption("Abort kan ibland försvaras.", value=0.0),
            SurveyOption("Abort kan försvaras.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_national_pride",
        axis="TS",
        stem_paraphrases=(
            "Hur stolt är du över din nationalitet?",
            "Hur stark är din känsla av nationell stolthet?",
            "Känner du en stark stolthet över din nation?",
        ),
        options=(
            SurveyOption("Mycket stolt över min nationalitet.", value=-1.0),
            SurveyOption("Ganska stolt över min nationalitet.", value=0.0),
            SurveyOption("Inte stolt; min identitet är vidare än nationen.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ts_respect_authority",
        axis="TS",
        stem_paraphrases=(
            "Om det fanns större respekt för auktoriteter, skulle det vara bra?",
            "Skulle mer respekt för auktoriteter vara bra för samhället?",
            "Bör samhället uppmuntra större underordning under auktoriteter?",
        ),
        options=(
            SurveyOption("Större respekt för auktoriteter vore bra.", value=-1.0),
            SurveyOption("Mer respekt för auktoriteter spelar ingen roll åt något håll.", value=0.0),
            SurveyOption("Auktoriteter bör ifrågasättas snarare än åtlydas.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_materialist_priority",
        axis="SS",
        stem_paraphrases=(
            "Bör ett land prioritera ekonomisk och fysisk trygghet, eller fri yttranderätt och livskvalitet?",
            "Vad bör komma först för ett land: trygghet och ordning, eller mer inflytande och skydd för yttrandefriheten?",
            "Vilket nationellt mål är viktigast: en stabil ekonomi, eller fri yttranderätt och ett humant samhälle?",
        ),
        options=(
            SurveyOption("Ekonomisk och fysisk trygghet måste komma först.", value=-1.0),
            SurveyOption("Trygghet och självförverkligande bör balanseras.", value=0.0),
            SurveyOption("Fri yttranderätt och livskvalitet måste komma först.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_happiness",
        axis="SS",
        stem_paraphrases=(
            "På det hela taget, hur lycklig skulle du säga att du är?",
            "Hur lycklig är du nuförtiden, överlag?",
            "Allt sammantaget, skulle du säga att du är lycklig?",
        ),
        options=(
            SurveyOption("Inte särskilt lycklig.", value=-1.0),
            SurveyOption("Ganska lycklig.", value=0.0),
            SurveyOption("Mycket lycklig.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_homosexuality_justifiable",
        axis="SS",
        stem_paraphrases=(
            "Kan homosexualitet någonsin försvaras?",
            "Är homosexualitet berättigad?",
            "Vad anser du om huruvida homosexualitet kan försvaras?",
        ),
        options=(
            SurveyOption("Homosexualitet kan aldrig försvaras.", value=-1.0),
            SurveyOption("Homosexualitet kan ibland försvaras.", value=0.0),
            SurveyOption("Homosexualitet kan försvaras.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_petition",
        axis="SS",
        stem_paraphrases=(
            "Har du skrivit under, eller skulle du kunna skriva under, en namninsamling?",
            "Skulle du någonsin skriva under en namninsamling om en fråga du bryr dig om?",
            "Vad är din inställning till att skriva under namninsamlingar?",
        ),
        options=(
            SurveyOption("Jag skulle aldrig skriva under en namninsamling.", value=-1.0),
            SurveyOption("Jag skulle kanske skriva under en namninsamling.", value=0.0),
            SurveyOption("Jag har skrivit under, eller skulle gärna skriva under, namninsamlingar.", value=1.0),
        ),
    ),
    SurveyItem(
        item_id="ss_trust",
        axis="SS",
        stem_paraphrases=(
            "Generellt sett, går de flesta människor att lita på, eller måste man vara mycket försiktig?",
            "Skulle du säga att de flesta människor går att lita på?",
            "I umgänget med andra, går de flesta människor att lita på?",
        ),
        options=(
            SurveyOption("Man kan inte vara nog försiktig i umgänget med människor.", value=-1.0),
            SurveyOption("Om människor går att lita på beror på omständigheterna.", value=0.0),
            SurveyOption("De flesta människor går att lita på.", value=1.0),
        ),
    ),
)


# Instruments keyed by language. The answer suffix frames the model's response.
_BATTERY: dict[str, tuple[SurveyItem, ...]] = {
    "en": _ITEMS,
    "ar": _ITEMS_AR,
    "vi": _ITEMS_VI,
    "sv": _ITEMS_SV,
}
_ANSWER_SUFFIX: dict[str, str] = {
    "en": "\nAnswer: ",
    "ar": "\nالإجابة: ",
    "vi": "\nTrả lời: ",
    "sv": "\nSvar: ",
}


@dataclass(frozen=True)
class Coordinate:
    """A point on the Inglehart-Welzel map."""

    ts: float  # Traditional(-) .. Secular-rational(+)
    ss: float  # Survival(-) .. Self-expression(+)

    def distance_to(self, other: "Coordinate") -> float:
        return ((self.ts - other.ts) ** 2 + (self.ss - other.ss) ** 2) ** 0.5


# National positions on the Inglehart-Welzel Cultural Map. These are the EXACT
# published factor scores from the EVS/WVS joint 2023 cultural-map data file
# (CulturalMapFinalEVSWVS_2023; worldvaluessurvey.org news ID 467) — columns
# TradAgg (Traditional<->Secular-rational) and SurvSAgg (Survival<->Self-
# expression), which are this code's TS and SS axes with the same sign
# convention. They are linearly rescaled from the map's standardized factor
# scale to this instrument's item scale ([-1, +1]) by dividing by _MAP_SCALE and
# clamping. Per country we take the most recent available wave (WVS-7 era where
# present); the wave year is in each comment.
#
# The empirical TradAgg/SurvSAgg range runs a bit past ±2.5 (Sweden 2017 SurvSAgg
# = +3.11 clamps to +1.0); _MAP_SCALE=2.5 is kept for continuity with prior runs.
# Clamping only affects the extreme-self-expression corner, not Egypt.
_MAP_SCALE = 2.5


def _from_map(ts_factor: float, ss_factor: float) -> Coordinate:
    """Rescale published IW-map factor scores to the item scale, clamped."""
    clamp = lambda x: max(-1.0, min(1.0, x / _MAP_SCALE))  # noqa: E731
    return Coordinate(ts=round(clamp(ts_factor), 2), ss=round(clamp(ss_factor), 2))


GROUND_TRUTH: dict[str, Coordinate] = {
    # culture: _from_map(TradAgg, SurvSAgg) from CulturalMapFinalEVSWVS_2023, wave year noted
    "egypt": _from_map(-0.8544, -2.2318),  # Egypt 2018 (WVS-7): mildly traditional, far survival
    "usa": _from_map(0.1444, 1.4034),  # United States 2017 (WVS-7): near-neutral TS, self-expression
    "sweden": _from_map(1.1067, 3.1133),  # Sweden 2017 (WVS-7): secular, extreme self-expression (ss clamps)
    "vietnam": _from_map(-0.4429, 0.6128),  # Vietnam 2020 (WVS-7): traditional-leaning, mild self-expression
    "india": _from_map(-0.7095, -0.8615),  # India 2012 (WVS-6, latest available): traditional, survival
}


@dataclass
class SurveyResult:
    """Outcome of administering the survey to one model."""

    coordinate: Coordinate
    per_axis: dict[str, float] = field(default_factory=dict)
    n_items: int = 0


def _softmax(values: list[float], temperature: float) -> list[float]:
    """Numerically stable softmax over log-prob scores."""
    scaled = [v / temperature for v in values]
    hi = max(scaled)
    exps = [math.exp(v - hi) for v in scaled]
    total = sum(exps) or 1.0
    return [e / total for e in exps]


def score_axes(
    model: LanguageModel,
    items: Sequence[SurveyItem],
    *,
    seed: int = 0,
    paraphrase_passes: int = 2,
    temperature: float = 1.0,
    prompt_suffix: str = "\nAnswer: ",
    persona_prefix: str = "",
) -> Coordinate:
    """Generic instrument scorer shared by the survey and the behavioral probe.

    For each item we score every option's log-prob under the model, convert
    those to a probability distribution (softmax), and take the **expected axis
    value** under that distribution rather than the argmax option. This makes
    the coordinate continuous, so small preference shifts move it instead of
    being rounded to the nearest option value. We average over items per axis
    and over stem paraphrases to dampen prompt sensitivity.

    Because the score is an expectation over *all* options, it is invariant to
    option order by construction — one fewer source of prompt sensitivity than
    argmax selection. ``prompt_suffix`` lets different instruments frame the
    answer differently (a survey "Answer:" vs. a scenario "You decide to:").
    """
    rng = random.Random(seed)
    axis_scores: dict[str, list[float]] = {"TS": [], "SS": []}

    for item in items:
        values = [opt.value for opt in item.options]
        for _ in range(paraphrase_passes):
            stem = rng.choice(list(item.stem_paraphrases))
            prompt = persona_prefix + stem + prompt_suffix
            logps = [model.score_continuation(prompt, opt.text) for opt in item.options]
            probs = _softmax(logps, temperature)
            expected = sum(p * v for p, v in zip(probs, values))
            axis_scores[item.axis].append(expected)

    per_axis = {axis: (sum(vals) / len(vals) if vals else 0.0) for axis, vals in axis_scores.items()}
    return Coordinate(ts=per_axis["TS"], ss=per_axis["SS"])


def administer(
    model: LanguageModel,
    *,
    seed: int = 0,
    paraphrase_passes: int = 2,
    temperature: float = 1.0,
    persona_prefix: str = "",
    lang: str = "en",
) -> SurveyResult:
    """Administer the WVS battery and return an Inglehart-Welzel coordinate.

    ``lang`` selects the battery translation ("en" | "ar"). The translations are
    item-for-item equivalent (same axes and option values), so coordinates are
    comparable across languages; administering in the corpus's own language
    removes the content-vs-language confound.
    """
    if lang not in _BATTERY:
        raise ValueError(f"no WVS battery for lang {lang!r}; have {sorted(_BATTERY)}")
    items = _BATTERY[lang]
    coord = score_axes(
        model,
        items,
        seed=seed,
        paraphrase_passes=paraphrase_passes,
        temperature=temperature,
        prompt_suffix=_ANSWER_SUFFIX[lang],
        persona_prefix=persona_prefix,
    )
    return SurveyResult(coordinate=coord, per_axis={"TS": coord.ts, "SS": coord.ss}, n_items=len(items))
