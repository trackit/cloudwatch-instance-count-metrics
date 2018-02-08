resource "aws_lambda_function" "instance_metrics" {
  function_name = "put-instance-count-metrics"
  filename = "${data.archive_file.instance_metrics_source.output_path}"
  handler = "lambda.lambda_handler"
  role = "${aws_iam_role.instance_metrics.arn}"
  runtime = "python3.6"
  source_code_hash = "${data.archive_file.instance_metrics_source.output_base64sha256}"
}

resource "aws_lambda_permission" "instance_metrics" {
  statement_id  = "AllowScheduledExecution"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.instance_metrics.arn}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.instance_metrics_ticker.arn}"
}

resource "aws_cloudwatch_event_rule" "instance_metrics_ticker" {
  name                = "check_instance_count"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "instance_metrics" {
  rule = "${aws_cloudwatch_event_rule.instance_metrics_ticker.name}"
  arn  = "${aws_lambda_function.instance_metrics.arn}"
}

data "archive_file" "instance_metrics_source" {
  type        = "zip"
  output_path = "${path.module}/src/lambda.zip"

  source {
    content  = "${file("${path.module}/src/lambda.py")}"
    filename = "lambda.py"
  }
}
