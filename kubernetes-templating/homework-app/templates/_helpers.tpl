{{/*
Chart name
*/}}
{{- define "homework-app.name" -}}
{{- default .Chart.Name .Values.nameOverride }}
{{- end }}

{{/*
Full name
*/}}
{{- define "homework-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "homework-app.name" .) }}
{{- end }}
{{- end }}