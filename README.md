# EC2 Instance count metrics producer

This repository contains the Terraform configuration and Python code for a
lambda function which periodically reads the list of all instances and that of
all reserved instances to produce useful CloudWatch metrics:

* On-demand instance count per type, AZ, tenancy and platform;
* Reserved instance count per type, AZ, tenancy and platform;
* Count of on-demand instances benefitting from instance reservations
  (estimation) per type, AZ, tenancy and platform;
* Count of reserved instances match by no on-demand instances per type, AZ,
  tenancy and platform;

## Deployment

### Requirements

In order to deploy this you need to have AWS credentials configured using any
of the standard ways supported by the AWS SDKs, and you need to have an up to
date version of Terraform installed.

### Process

1. Edit `provider.tf` to set the region you want the metrics to be generated in.
2. Run `terraform init`
3. Run `terraform apply`
4. Metrics should appear soon in CloudWatch under the “Trackit” namespace.
