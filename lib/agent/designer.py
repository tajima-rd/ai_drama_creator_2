# lib/agent/designer.py

from .base_agent import BaseAgent
from ..core.project import Project
from ..schema import (
    Report,
    Agenda,
    Character,
    PlotDesign,
    RegionSummary,
)

class DesignerAgent(BaseAgent):
    def __init__(
            self, 
            text_generator, 
            project: Project, 
            agenda: Agenda=None, 
            report:Report=None, 
            protagonist: Character = None, 
            deuteragonist: Character = None, 
            region_summary: RegionSummary = None
        ):
        
        super().__init__(text_generator)
        self.project = project
        self.report = report
        self.agenda = agenda
        self.protagonist = protagonist
        self.deuteragonist = deuteragonist
        self.region_summary = region_summary
    
    def compose_agenda(self):
        agenda_path = self.project.results["agenda"]

        if not agenda_path.exists():
            # --- 生成モード ---
            self.agenda = self._create_agenda_sequential()
            print(f"Agenda generated and saved to: {agenda_path}")
        else:
            # --- ロードモード ---
            agenda_data = self.load_json(agenda_path)
            self.agenda = Agenda(**agenda_data)
            print(f"Agenda loaded from: {agenda_path}")
            
        return self.agenda

    def design_plot(self):
        plot_path = self.project.results["plot"]

        if not plot_path.exists():
            plot_design = self._create_plot_sequential()
            print(f"Plot generated and saved to: {plot_path}")
        else:
            # ロードモード
            plot_data = self.load_json(plot_path)
            plot_design = PlotDesign(**plot_data)
            print(f"Plot loaded from: {plot_path}")

        return plot_design

    def _create_agenda_sequential(self) -> Agenda:
        agenda = Agenda(title="", overview="", needs="", seeds="", planning="", concept="")

        context = (
            "あなたはストーリー設計に精通したストーリー・デザイナーです。現地体験型の音声ドラマ企画を考えます。\n\n"
            "現地体験型の音声ドラマは、スマートフォンの位置情報を使い、特定の場所に近づくと音声が再生される仕組みです"
            "（Sony の「Locatone」というサービスの利用を想定）。\n\n"
            "以下は、これまでの分析で得られた情報です。\n"
            f"【背景情報】\n{self.report.background}\n\n"
            f"【潜在ニーズ分析の結果】\n{self.report.potential_needs}\n\n"
            f"【潜在シーズ分析の結果】\n{self.report.potential_seeds}\n\n"
            f"【ターゲット層】\n{self.report.target_layer}\n"
        )
        conversation_history = [{"role": "system", "content": context}]

        common_constraints = (
            "\n\n【回答時の制約】\n"
            "- 挨拶や前置き、見出し記号（#, ### 等）は一切不要です。本文のみを出力してください。\n"
            "- 「である調」で記述してください。\n"
            "- ストーリーの具体的な内容（固有名詞やエピソード）はまだ含めず、概念設計に留めてください。\n"
            "- 対象地域に含まれない情報を含めないでください。\n"
        )

        agenda.overview = self._ask_sequential(
            conversation_history,
            "上記の情報を踏まえ、この地域の観光における『現状』を整理してください。",
            "（1000字程度）",
            common_constraints,
        )
        agenda.needs = self._ask_sequential(
            conversation_history,
            "現状を踏まえ、将来に向けて拡大するべき『ニーズ』を検討してください。",
            "（1000字程度）",
            common_constraints,
        )
        agenda.seeds = self._ask_sequential(
            conversation_history,
            "現状とニーズを踏まえ、将来に向けて売り出していきたい『シーズ（地域資源）』を検討してください。",
            "（1000字程度）",
            common_constraints,
        )
        agenda.planning = self._ask_sequential(
            conversation_history,
            "現状・ニーズ・シーズを踏まえ、現地体験型の音声ドラマの『企画内容』を提案してください。",
            "（1000字程度）",
            common_constraints,
        )
        agenda.concept = self._ask_sequential(
            conversation_history,
            "ここまでの内容を踏まえ、ターゲット層に向けた『ストーリー概念（ストーリーの方向性）』を提案してください。",
            "（1000字程度）",
            common_constraints,
        )
        agenda.title = self._ask_title(
            conversation_history,
            "ここまでの企画内容とストーリー概念に合致する、この企画の『タイトル』を1つだけ提案してください。",
            common_constraints,
        )

        agenda.save_json(self.project.results["agenda"])
        return agenda

    def _create_plot_sequential(self) -> PlotDesign:
        plot = PlotDesign(title="", synopsis="", emotional_arc="", narrative_integration="")

        context = (
            "あなたはストーリー構成と観光体験設計に精通したストーリーデザイナーです。\n"
            "与えられた企画内容、キャラクタープロファイル、地域概要に基づいて、"
            "ストーリー・プロット設計書を作成します。\n\n"
            f"【企画内容】\n{self.agenda.planning}\n\n"
            f"【ストーリー概念】\n{self.agenda.concept}\n\n"
            f"【プロタゴニスト】\n{self._describe_character(self.protagonist)}\n\n"
            f"【デュオタゴニスト】\n{self._describe_character(self.deuteragonist)}\n\n"
            f"【地域概要】\n{self.region_summary.summary}\n\n"
            f"【地域特性】\n{self.region_summary.features}\n"
        )
        conversation_history = [{"role": "system", "content": context}]

        common_constraints = (
            "\n\n【制約条件】\n"
            "- 挨拶や前置きは不要。本文のみを出力してください。\n"
            "- スポット（位置情報ポイント）の細かな列挙は行わないでください。各スポットを巡る順番に"
            "依存しない範囲の内容に留めてください。\n"
            "- キャラクターの細かいセリフや会話劇にはしないでください。\n"
            "- 「観光案内」ではなく「体験としてのストーリー」になる語りにしてください。\n"
        )

        plot.synopsis = self._ask_sequential(
            conversation_history,
            "上記の情報を踏まえ、物語全体の『あらすじ』を作成してください。冒頭で主人公が旅に出る"
            "理由と心情を示し、出会い・心の揺れ・転機・成長を盛り込み、結末は解決しすぎず"
            "『変化の余韻』で締めてください。",
            "（800〜1200字程度）",
            common_constraints,
        )
        plot.emotional_arc = self._ask_sequential(
            conversation_history,
            "上記のあらすじを踏まえ、物語を通じた主人公たちの『感情変化のプロセス』をまとめてください。",
            "（200字程度）",
            common_constraints,
        )
        plot.narrative_integration = self._ask_sequential(
            conversation_history,
            "上記のあらすじを踏まえ、地域資源（シーズ）やニーズをどのようにストーリーへ織り込んだかを"
            "解説してください。",
            "（200字程度）",
            common_constraints,
        )
        plot.title = self._ask_title(
            conversation_history,
            "ここまでの内容に合致する、この物語の『タイトル』を1つだけ提案してください。",
            common_constraints,
        )

        plot.save_json(self.project.results["plot"])
        return plot