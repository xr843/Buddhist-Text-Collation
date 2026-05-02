"""
学习辅助服务 - 闪卡、进度追踪、测验
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import random


class LearningService:
    """学习辅助服务"""

    def __init__(self):
        # 内存存储
        self._decks_db: Dict[int, Dict[str, Any]] = {}
        self._cards_db: Dict[int, Dict[str, Any]] = {}
        self._progress_db: Dict[int, Dict[str, Any]] = {}  # card_id -> progress
        self._quiz_history: List[Dict[str, Any]] = []

        self._deck_id_counter = 1
        self._card_id_counter = 1

        # 初始化示例数据
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例闪卡库"""
        # 创建示例卡组
        deck1 = self.create_deck(
            title="佛典标点符号",
            description="常见佛典标点符号的用法和含义",
            category="标点研究"
        )

        # 添加示例闪卡
        cards = [
            {
                "front": "句号（。）在佛典中的主要用法",
                "back": "1. 表示陈述句结束\n2. 用于偈颂每句末尾\n3. 标示经文段落结束",
                "tags": ["标点", "基础"]
            },
            {
                "front": "问号（？）在佛典对话中的用法",
                "back": "1. 用于佛陀与弟子的问答\n2. 表示疑问或反问\n3. 常见于「云何」「何以故」等问句后",
                "tags": ["标点", "对话"]
            },
            {
                "front": "顿号（、）的使用场景",
                "back": "1. 并列名相之间\n2. 连续列举时\n3. 如「色、受、想、行、识」",
                "tags": ["标点", "基础"]
            },
            {
                "front": "引号的两种用法",
                "back": "1. 直接引语：引用佛陀或他人原话\n2. 特殊强调：专有名词、术语\n3. 如「如是我闻」",
                "tags": ["标点", "进阶"]
            },
            {
                "front": "冒号（：）的典型用法",
                "back": "1. 引出说话内容\n2. 如「佛言：」「告诸比丘：」\n3. 引出解释或列举",
                "tags": ["标点", "基础"]
            }
        ]

        for card in cards:
            self.create_card(
                deck_id=deck1["id"],
                front=card["front"],
                back=card["back"],
                tags=card["tags"]
            )

        # 创建术语卡组
        deck2 = self.create_deck(
            title="佛学基本术语",
            description="常见佛学术语的解释",
            category="佛学知识"
        )

        terms = [
            {
                "front": "五蕴",
                "back": "色、受、想、行、识。\n构成有情众生的五种要素，说明「我」是五蕴和合的假名，无实在自性。",
                "tags": ["术语", "基础"]
            },
            {
                "front": "四谛",
                "back": "苦、集、灭、道。\n苦谛：人生是苦\n集谛：苦的原因\n灭谛：苦的止息\n道谛：灭苦之道",
                "tags": ["术语", "基础"]
            },
            {
                "front": "八正道",
                "back": "正见、正思维、正语、正业、正命、正精进、正念、正定。\n通往解脱的修行方法。",
                "tags": ["术语", "修行"]
            },
            {
                "front": "三法印",
                "back": "诸行无常、诸法无我、涅槃寂静。\n用以印证佛法真伪的三个标准。",
                "tags": ["术语", "核心"]
            },
            {
                "front": "缘起",
                "back": "「此有故彼有，此生故彼生；此无故彼无，此灭故彼灭。」\n一切事物都是因缘和合而生，没有独立存在的实体。",
                "tags": ["术语", "核心"]
            }
        ]

        for term in terms:
            self.create_card(
                deck_id=deck2["id"],
                front=term["front"],
                back=term["back"],
                tags=term["tags"]
            )

    # ==================== 卡组管理 ====================

    def create_deck(
        self,
        title: str,
        description: str = "",
        category: str = ""
    ) -> Dict[str, Any]:
        """创建闪卡卡组"""
        deck_id = self._deck_id_counter
        self._deck_id_counter += 1

        now = datetime.now().isoformat()
        deck = {
            "id": deck_id,
            "title": title,
            "description": description,
            "category": category,
            "card_count": 0,
            "created_at": now,
            "updated_at": now
        }

        self._decks_db[deck_id] = deck
        return deck

    def list_decks(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取卡组列表"""
        decks = list(self._decks_db.values())

        if category:
            decks = [d for d in decks if d["category"] == category]

        # 更新卡片数量
        for deck in decks:
            deck["card_count"] = len([
                c for c in self._cards_db.values()
                if c["deck_id"] == deck["id"]
            ])

        return sorted(decks, key=lambda x: x["updated_at"], reverse=True)

    def get_deck(self, deck_id: int) -> Optional[Dict[str, Any]]:
        """获取卡组详情"""
        return self._decks_db.get(deck_id)

    def update_deck(
        self,
        deck_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """更新卡组"""
        deck = self._decks_db.get(deck_id)
        if not deck:
            return None

        if title is not None:
            deck["title"] = title
        if description is not None:
            deck["description"] = description
        if category is not None:
            deck["category"] = category

        deck["updated_at"] = datetime.now().isoformat()
        return deck

    def delete_deck(self, deck_id: int) -> bool:
        """删除卡组及其所有卡片"""
        if deck_id not in self._decks_db:
            return False

        # 删除相关卡片和进度
        card_ids = [
            cid for cid, c in self._cards_db.items()
            if c["deck_id"] == deck_id
        ]
        for cid in card_ids:
            del self._cards_db[cid]
            if cid in self._progress_db:
                del self._progress_db[cid]

        del self._decks_db[deck_id]
        return True

    # ==================== 闪卡管理 ====================

    def create_card(
        self,
        deck_id: int,
        front: str,
        back: str,
        tags: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """创建闪卡"""
        if deck_id not in self._decks_db:
            return None

        card_id = self._card_id_counter
        self._card_id_counter += 1

        now = datetime.now().isoformat()
        card = {
            "id": card_id,
            "deck_id": deck_id,
            "front": front,
            "back": back,
            "tags": tags or [],
            "created_at": now,
            "updated_at": now
        }

        self._cards_db[card_id] = card

        # 初始化学习进度
        self._progress_db[card_id] = {
            "card_id": card_id,
            "times_reviewed": 0,
            "times_correct": 0,
            "last_reviewed": None,
            "mastery_level": 0,  # 0-5 熟练度
            "next_review": now
        }

        # 更新卡组时间
        self._decks_db[deck_id]["updated_at"] = now

        return card

    def list_cards(self, deck_id: int) -> List[Dict[str, Any]]:
        """获取卡组中的所有卡片"""
        cards = [c for c in self._cards_db.values() if c["deck_id"] == deck_id]

        # 附加进度信息
        for card in cards:
            progress = self._progress_db.get(card["id"], {})
            card["progress"] = progress

        return sorted(cards, key=lambda x: x["created_at"])

    def get_card(self, card_id: int) -> Optional[Dict[str, Any]]:
        """获取闪卡详情"""
        card = self._cards_db.get(card_id)
        if card:
            card["progress"] = self._progress_db.get(card_id, {})
        return card

    def update_card(
        self,
        card_id: int,
        front: Optional[str] = None,
        back: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """更新闪卡"""
        card = self._cards_db.get(card_id)
        if not card:
            return None

        if front is not None:
            card["front"] = front
        if back is not None:
            card["back"] = back
        if tags is not None:
            card["tags"] = tags

        card["updated_at"] = datetime.now().isoformat()
        return card

    def delete_card(self, card_id: int) -> bool:
        """删除闪卡"""
        if card_id not in self._cards_db:
            return False

        del self._cards_db[card_id]
        if card_id in self._progress_db:
            del self._progress_db[card_id]

        return True

    # ==================== 学习功能 ====================

    def get_study_cards(self, deck_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """获取待学习的卡片（优先低熟练度）"""
        cards = [c for c in self._cards_db.values() if c["deck_id"] == deck_id]

        # 按熟练度和上次复习时间排序
        def sort_key(card):
            progress = self._progress_db.get(card["id"], {})
            mastery = progress.get("mastery_level", 0)
            last_reviewed = progress.get("last_reviewed") or "1970-01-01"
            return (mastery, last_reviewed)

        cards.sort(key=sort_key)

        # 添加进度信息
        result = cards[:count]
        for card in result:
            card["progress"] = self._progress_db.get(card["id"], {})

        return result

    def record_review(
        self,
        card_id: int,
        is_correct: bool,
        difficulty: int = 3  # 1-5, 1最难5最易
    ) -> Dict[str, Any]:
        """记录复习结果"""
        if card_id not in self._cards_db:
            return {"success": False, "error": "卡片不存在"}

        progress = self._progress_db.get(card_id)
        if not progress:
            progress = {
                "card_id": card_id,
                "times_reviewed": 0,
                "times_correct": 0,
                "last_reviewed": None,
                "mastery_level": 0,
                "next_review": datetime.now().isoformat()
            }
            self._progress_db[card_id] = progress

        now = datetime.now().isoformat()
        progress["times_reviewed"] += 1
        progress["last_reviewed"] = now

        if is_correct:
            progress["times_correct"] += 1
            # 根据难度调整熟练度
            if difficulty >= 4:
                progress["mastery_level"] = min(5, progress["mastery_level"] + 1)
            elif difficulty <= 2:
                progress["mastery_level"] = max(0, progress["mastery_level"] - 1)
        else:
            progress["mastery_level"] = max(0, progress["mastery_level"] - 1)

        return {
            "success": True,
            "progress": progress,
            "mastery_level": progress["mastery_level"]
        }

    # ==================== 测验功能 ====================

    def generate_quiz(
        self,
        deck_id: int,
        question_count: int = 5,
        quiz_type: str = "multiple_choice"
    ) -> Dict[str, Any]:
        """生成测验"""
        cards = [c for c in self._cards_db.values() if c["deck_id"] == deck_id]

        if len(cards) < 2:
            return {"success": False, "error": "卡片数量不足"}

        # 随机选择题目
        selected = random.sample(cards, min(question_count, len(cards)))

        questions = []
        for card in selected:
            if quiz_type == "multiple_choice":
                # 生成选项（1个正确 + 3个干扰项）
                other_cards = [c for c in cards if c["id"] != card["id"]]
                wrong_answers = random.sample(
                    other_cards,
                    min(3, len(other_cards))
                )

                options = [card["back"]] + [c["back"] for c in wrong_answers]
                random.shuffle(options)

                questions.append({
                    "id": card["id"],
                    "question": card["front"],
                    "options": options,
                    "correct_index": options.index(card["back"]),
                    "type": "multiple_choice"
                })
            else:  # fill_blank
                questions.append({
                    "id": card["id"],
                    "question": card["front"],
                    "answer": card["back"],
                    "type": "fill_blank"
                })

        quiz = {
            "deck_id": deck_id,
            "deck_title": self._decks_db[deck_id]["title"],
            "questions": questions,
            "total": len(questions),
            "created_at": datetime.now().isoformat()
        }

        return {"success": True, "quiz": quiz}

    def submit_quiz(
        self,
        deck_id: int,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提交测验答案"""
        correct_count = 0
        results = []

        for answer in answers:
            card_id = answer.get("card_id")
            user_answer = answer.get("answer")
            is_correct = answer.get("is_correct", False)

            if is_correct:
                correct_count += 1

            # 记录复习
            self.record_review(card_id, is_correct, difficulty=4 if is_correct else 2)

            results.append({
                "card_id": card_id,
                "is_correct": is_correct,
                "user_answer": user_answer
            })

        # 记录测验历史
        history = {
            "deck_id": deck_id,
            "total": len(answers),
            "correct": correct_count,
            "score": round(correct_count / len(answers) * 100, 1) if answers else 0,
            "results": results,
            "completed_at": datetime.now().isoformat()
        }
        self._quiz_history.append(history)

        return {
            "success": True,
            "score": history["score"],
            "correct": correct_count,
            "total": len(answers),
            "results": results
        }

    # ==================== 统计功能 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        total_decks = len(self._decks_db)
        total_cards = len(self._cards_db)

        # 计算已掌握的卡片（熟练度>=4）
        mastered = sum(
            1 for p in self._progress_db.values()
            if p.get("mastery_level", 0) >= 4
        )

        # 计算复习次数
        total_reviews = sum(
            p.get("times_reviewed", 0)
            for p in self._progress_db.values()
        )

        # 计算正确率
        total_correct = sum(
            p.get("times_correct", 0)
            for p in self._progress_db.values()
        )
        accuracy = round(total_correct / total_reviews * 100, 1) if total_reviews > 0 else 0

        # 测验统计
        quiz_count = len(self._quiz_history)
        avg_score = 0
        if quiz_count > 0:
            avg_score = round(
                sum(q["score"] for q in self._quiz_history) / quiz_count,
                1
            )

        return {
            "total_decks": total_decks,
            "total_cards": total_cards,
            "cards_mastered": mastered,
            "mastery_rate": round(mastered / total_cards * 100, 1) if total_cards > 0 else 0,
            "total_reviews": total_reviews,
            "accuracy_rate": accuracy,
            "quiz_count": quiz_count,
            "avg_quiz_score": avg_score
        }

    def get_deck_statistics(self, deck_id: int) -> Dict[str, Any]:
        """获取单个卡组的统计"""
        cards = [c for c in self._cards_db.values() if c["deck_id"] == deck_id]

        mastered = 0
        learning = 0
        new = 0
        total_reviews = 0
        total_correct = 0

        for card in cards:
            progress = self._progress_db.get(card["id"], {})
            mastery = progress.get("mastery_level", 0)
            reviews = progress.get("times_reviewed", 0)
            correct = progress.get("times_correct", 0)

            total_reviews += reviews
            total_correct += correct

            if mastery >= 4:
                mastered += 1
            elif reviews > 0:
                learning += 1
            else:
                new += 1

        return {
            "total_cards": len(cards),
            "mastered": mastered,
            "learning": learning,
            "new": new,
            "total_reviews": total_reviews,
            "accuracy_rate": round(total_correct / total_reviews * 100, 1) if total_reviews > 0 else 0
        }


# 单例
learning_service = LearningService()
