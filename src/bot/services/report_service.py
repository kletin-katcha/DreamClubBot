from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.report import Report

class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report(self, guild_id: int, reporter_id: int, target_id: int, reason: str, content: str = None, proof: str = None) -> Report:
        report = Report(
            guild_id=guild_id,
            reporter_id=reporter_id,
            target_id=target_id,
            reason=reason,
            message_content=content,
            attachment_url=proof,
            status="pending"
        )
        self.session.add(report)
        await self.session.commit()
        return report

    async def update_status(self, report_id: int, status: str):
        report = await self.session.get(Report, report_id)
        if report:
            report.status = status
            self.session.add(report)
            await self.session.commit()