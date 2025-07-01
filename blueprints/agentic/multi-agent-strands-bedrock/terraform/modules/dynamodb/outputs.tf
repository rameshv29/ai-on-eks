output "weather_agent_table_name" {
  description = "The Name of DynamodDb Table for Weather Agent"
  value       = aws_dynamodb_table.weather_agent_state_table.name
}
