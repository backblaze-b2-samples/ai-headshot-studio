import { SubjectDetail } from "@/components/gallery/subject-detail";

export default async function SubjectDetailPage({
  params,
}: {
  params: Promise<{ subjectId: string }>;
}) {
  const { subjectId } = await params;
  return <SubjectDetail subjectId={subjectId} />;
}
