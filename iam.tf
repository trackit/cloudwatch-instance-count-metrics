resource "aws_iam_role" "instance_metrics" {
  name               = "put-instance-count-metrics"
  assume_role_policy = "${data.aws_iam_policy_document.lambda_assume_role.json}"
}

resource "aws_iam_role_policy" "instance_metrics" {
  name   = "put-instance-count-metrics"
  role   = "${aws_iam_role.instance_metrics.name}"
  policy = "${data.aws_iam_policy_document.instance_metrics_policy.json}"
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]

    principals {
      type = "Service"

      identifiers = [
        "lambda.amazonaws.com",
      ]
    }
  }
}

data "aws_iam_policy_document" "instance_metrics_policy" {
  statement {
    actions = [
      "ec2:DescribeInstances",
      "ec2:DescribeReservedInstances",
      "cloudwatch:PutMetricData",
    ]

    resources = ["*"]
  }
}
