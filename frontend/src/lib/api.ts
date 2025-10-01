export async function inspectBcf(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("http://localhost:8000/bcf/inspect", {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function mergeBcfs(files: File[]) {
  const formData = new FormData();
  files.forEach(f => formData.append("files", f));
  const res = await fetch("http://localhost:8000/bcf/merge", {
    method: "POST",
    body: formData,
  });
  return res.blob(); // download merged bcfzip
}
